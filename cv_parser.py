import os
import re
import json
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

import PyPDF2
import pdfplumber
from docx import Document
import spacy
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class CVParser:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.stop_words = set(stopwords.words('english'))
        self.cv_content = ""
        self.cv_sections = {}
        self.cv_entities = {}
        self.is_loaded = False
        
    def load_cv(self, file_path: str) -> bool:
        """Load and parse a CV file"""
        try:
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension == '.pdf':
                content = self._extract_pdf_content(file_path)
            elif file_extension in ['.docx', '.doc']:
                content = self._extract_docx_content(file_path)
            elif file_extension == '.txt':
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            if content.strip():
                self.cv_content = content
                self._parse_cv_sections()
                self._extract_entities()
                self.is_loaded = True
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error loading CV: {str(e)}")
            return False
    
    def _extract_pdf_content(self, file_path: str) -> str:
        """Extract text content from PDF file"""
        content = ""
        
        try:
            # Try using pdfplumber first (better for complex layouts)
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        content += text + "\n"
        except:
            # Fallback to PyPDF2
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        content += page.extract_text() + "\n"
            except Exception as e:
                raise Exception(f"Failed to extract PDF content: {str(e)}")
        
        return content
    
    def _extract_docx_content(self, file_path: str) -> str:
        """Extract text content from DOCX file"""
        try:
            doc = Document(file_path)
            content = ""
            for paragraph in doc.paragraphs:
                content += paragraph.text + "\n"
            return content
        except Exception as e:
            raise Exception(f"Failed to extract DOCX content: {str(e)}")
    
    def _parse_cv_sections(self):
        """Parse CV into logical sections"""
        sections = {
            'personal_info': [],
            'summary': [],
            'experience': [],
            'education': [],
            'skills': [],
            'clubs': [],
            'projects': [],
            'achievements': [],
            'other': []
        }
        
        # Common section headers
        section_patterns = {
            'personal_info': r'(personal|contact|details)',
            'summary': r'(summary|profile|objective|about)',
            'experience': r'(experience|employment|work|career|professional)',
            'education': r'(education|academic|qualification|degree)',
            'skills': r'(skills|competencies|technologies|technical)',
            'clubs': r'(clubs|unions)',
            'projects': r'(projects|portfolio)',
            'achievements': r'(achievements|awards|honors|accomplishments)'
        }
        
        lines = self.cv_content.split('\n')
        current_section = 'other'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line is a section header
            line_lower = line.lower()
            for section, pattern in section_patterns.items():
                if re.search(pattern, line_lower) and len(line) < 50:
                    current_section = section
                    break
            else:
                sections[current_section].append(line)
        
        self.cv_sections = {k: '\n'.join(v) for k, v in sections.items() if v}
    
    def _extract_entities(self):
        """Extract named entities from CV and improve company extraction"""
        doc = self.nlp(self.cv_content)
        entities = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'dates': [],
            'technologies': []
        }
        # spaCy extraction
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                entities['persons'].append(ent.text)
            elif ent.label_ in ["ORG", "COMPANY"]:
                entities['organizations'].append(ent.text)
            elif ent.label_ in ["GPE", "LOC"]:
                entities['locations'].append(ent.text)
            elif ent.label_ == "DATE":
                entities['dates'].append(ent.text)
        # Regex-based company extraction from experience section
        experience_section = self.cv_sections.get('experience', '')
        company_regex = r'\|\s*([A-Za-z0-9 &.,-]+)\s*\|'
        for line in experience_section.split('\n'):
            match = re.search(company_regex, line)
            if match:
                company = match.group(1).strip()
                # Avoid duplicates and empty strings
                if company and company not in entities['organizations']:
                    entities['organizations'].append(company)
        # Extract potential technologies (simple keyword matching)
        tech_keywords = [
            'python', 'java', 'javascript', 'react', 'node.js', 'sql', 'mongodb',
            'aws', 'docker', 'kubernetes', 'git', 'linux', 'tensorflow', 'pytorch',
            'html', 'css', 'angular', 'vue', 'django', 'flask', 'fastapi'
        ]
        content_lower = self.cv_content.lower()
        for tech in tech_keywords:
            if tech in content_lower:
                entities['technologies'].append(tech)
        self.cv_entities = entities
    
    def answer_question(self, question: str) -> Tuple[str, float, List[str]]:
        """Answer a question about the CV"""
        if not self.is_loaded:
            return "No CV loaded", 0.0, []
        
        question_lower = question.lower()
        relevant_sections = []
        confidence = 0.0
        
        # Question type detection and answering
        if any(word in question_lower for word in ['role', 'position', 'job', 'title']):
            answer, conf, sources = self._answer_role_question(question)
        elif any(word in question_lower for word in ['education', 'degree', 'study', 'university', 'college']):
            answer, conf, sources = self._answer_education_question(question)
        elif any(word in question_lower for word in ['skill', 'technology', 'programming', 'tech']):
            answer, conf, sources = self._answer_skills_question(question)
        elif any(word in question_lower for word in ['experience', 'work', 'company', 'employer']):
            answer, conf, sources = self._answer_experience_question(question)
        elif any(word in question_lower for word in ['project', 'built', 'developed']):
            answer, conf, sources = self._answer_projects_question(question)
        else:
            # General search in all content
            answer, conf, sources = self._general_search(question)
        
        return answer, conf, sources
    
    def _answer_role_question(self, question: str) -> Tuple[str, float, List[str]]:
        """Answer questions about roles/positions"""
        experience_section = self.cv_sections.get('experience', '')
        
        if not experience_section:
            return "No work experience information found in the CV.", 0.3, []
        
        # Look for job titles and recent positions
        lines = experience_section.split('\n')
        roles = []
        
        for line in lines:
            # Simple heuristic: lines that might contain job titles
            if any(word in line.lower() for word in ['engineer', 'developer', 'manager', 'analyst', 'director', 'lead', 'senior', 'junior']):
                roles.append(line.strip())
        
        if roles:
            if 'last' in question.lower() or 'recent' in question.lower() or 'current' in question.lower():
                answer = f"Your most recent role appears to be: {roles[0]}"
            else:
                answer = f"Your roles include: {', '.join(roles[:3])}"
            return answer, 0.8, ['experience']
        
        return "Could not identify specific roles in your CV.", 0.4, ['experience']
    
    def _answer_education_question(self, question: str) -> Tuple[str, float, List[str]]:
        """Answer questions about education"""
        education_section = self.cv_sections.get('education', '')
        
        if not education_section:
            return "No education information found in the CV.", 0.3, []
        
        return f"Education details: {education_section}", 0.7, ['education']
    
    def _answer_skills_question(self, question: str) -> Tuple[str, float, List[str]]:
        """Answer questions about skills"""
        skills_section = self.cv_sections.get('skills', '')
        technologies = self.cv_entities.get('technologies', [])
        
        if technologies:
            tech_list = ', '.join(set(technologies))
            answer = f"Technologies and skills mentioned: {tech_list}"
            confidence = 0.8
        elif skills_section:
            answer = f"Skills section: {skills_section[:200]}..."
            confidence = 0.7
        else:
            answer = "No specific skills section found, but may be mentioned throughout the CV."
            confidence = 0.4
        
        return answer, confidence, ['skills']
    
    def _answer_experience_question(self, question: str) -> Tuple[str, float, List[str]]:
        """Answer questions about work experience"""
        experience_section = self.cv_sections.get('experience', '')
        organizations = self.cv_entities.get('organizations', [])
        
        if organizations:
            org_list = ', '.join(set(organizations))
            answer = f"Companies/organizations mentioned: {org_list}"
            confidence = 0.8
        elif experience_section:
            answer = f"Work experience: {experience_section[:200]}..."
            confidence = 0.7
        else:
            answer = "No work experience section found."
            confidence = 0.3
        
        return answer, confidence, ['experience']
    
    def _answer_projects_question(self, question: str) -> Tuple[str, float, List[str]]:
        """Answer questions about projects"""
        projects_section = self.cv_sections.get('projects', '')
        
        if projects_section:
            return f"Projects: {projects_section[:200]}...", 0.7, ['projects']
        else:
            return "No dedicated projects section found.", 0.3, []
    
    def _general_search(self, question: str) -> Tuple[str, float, List[str]]:
        """General search across all CV content"""
        question_words = [word.lower() for word in word_tokenize(question) if word.lower() not in self.stop_words]
        
        best_match = ""
        best_score = 0
        sources = []
        
        # Search in each section
        for section_name, content in self.cv_sections.items():
            if not content:
                continue
                
            content_words = [word.lower() for word in word_tokenize(content) if word.lower() not in self.stop_words]
            
            # Simple word overlap scoring
            overlap = len(set(question_words) & set(content_words))
            score = overlap / max(len(question_words), 1)
            
            if score > best_score:
                best_score = score
                best_match = content[:300] + "..."
                sources = [section_name]
        
        if best_score > 0.1:
            return best_match, best_score, sources
        else:
            return "I couldn't find relevant information in the CV to answer that question.", 0.2, []
    
    def get_cv_summary(self) -> Dict[str, Any]:
        """Get a summary of the loaded CV"""
        if not self.is_loaded:
            return {"error": "No CV loaded"}
        
        return {
            "sections": list(self.cv_sections.keys()),
            "entities": self.cv_entities,
            "word_count": len(word_tokenize(self.cv_content)),
            "sections_preview": {k: v[:100] + "..." if len(v) > 100 else v 
                               for k, v in self.cv_sections.items()}
        }
    
    def is_cv_loaded(self) -> bool:
        """Check if a CV is currently loaded"""
        return self.is_loaded
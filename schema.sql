CREATE DATABASE IF NOT EXISTS job_tracker;
USE job_tracker;

DROP TABLE IF EXISTS applications;
DROP TABLE IF EXISTS contacts;
DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS companies;

-- companies
CREATE TABLE companies (
company_id INT PRIMARY KEY AUTO_INCREMENT,
company_name VARCHAR(100) NOT NULL,
industry VARCHAR(50),
website VARCHAR(200),
city VARCHAR(50),
state VARCHAR(50),
notes TEXT
);

-- jobs
CREATE TABLE jobs (
job_id INT PRIMARY KEY AUTO_INCREMENT,
company_id INT NOT NULL,
job_title VARCHAR(100) NOT NULL,
job_type ENUM('Full-time', 'Part-time', 'Contract', 'Internship'),
salary_min INT, 
salary_max INT,
job_url VARCHAR(300),
date_posted DATE,
requirements JSON,
FOREIGN KEY (company_id) REFERENCES companies (company_id) ON DELETE CASCADE
);

-- applications
CREATE TABLE applications (
application_id INT PRIMARY KEY AUTO_INCREMENT,
job_id INT NOT NULL,
application_date DATE NOT NULL,
status ENUM('Applied', 'Screening', 'Interview', 'Offer', 'Rejected', 'Withdrawn'),
resume_version VARCHAR(50),
cover_letter_sent BOOLEAN,
interview_data JSON,
FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);

-- contacts
CREATE TABLE contacts (
contact_id INT PRIMARY KEY AUTO_INCREMENT,
company_id INT NOT NULL,
contact_name VARCHAR(100) NOT NULL,
title VARCHAR(100),
email VARCHAR(100),
phone VARCHAR(20),
linkedin_url VARCHAR(200),
notes TEXT,
FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

-- sample data
INSERT INTO companies (company_name, industry, website, city, state, notes) VALUES
('TechCorp',        'Technology',       'https://www.techcorp.example',    'Miami',   'Florida',    'Referred by a classmate'),
('DataCo',          'Data Analytics',   'https://www.dataco.example',      'Austin',  'Texas',      NULL),
('CloudNine Systems','Cloud Computing', 'https://www.cloudnine.example',   'Seattle', 'Washington', 'Fully remote friendly'),
('HealthBridge',    'Healthcare IT',    'https://www.healthbridge.example','Tampa',   'Florida',    NULL),
('BrightPath AI',   'AI/ML',            'https://www.brightpath.example',  'Orlando', 'Florida',    'Small startup, fast hiring');

INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max, job_url, date_posted, requirements) VALUES
(1, 'Software Developer','Full-time',  75000,  95000, 'https://www.techcorp.example/jobs/1',  '2026-10-12',
 '{"required_skills": ["Python","SQL","Flask"], "preferred_skills": ["Docker","AWS"], "education": "Bachelor in CS or related field", "experience_years": 1, "remote_option": true}'),
(2, 'Data Analyst','Full-time',  65000,  85000, 'https://www.dataco.example/jobs/2',    '2026-10-15',
 '{"required_skills": ["SQL","Excel","Tableau"], "preferred_skills": ["Python","R"], "education": "Bachelor degree", "experience_years": 1, "remote_option": false}'),
(3, 'Cloud Engineer','Full-time',  90000, 120000, 'https://www.cloudnine.example/jobs/3', '2026-10-20',
 '{"required_skills": ["AWS","Python","Linux"], "preferred_skills": ["Terraform"], "education": "Bachelor in CS", "experience_years": 3, "remote_option": true}'),
(1, 'Backend Intern','Internship', 20000,  28000, 'https://www.techcorp.example/jobs/4',  '2026-10-25',
 '{"required_skills": ["Python","Git","SQL"], "preferred_skills": ["Flask"], "education": "Currently enrolled in CS", "experience_years": 0, "remote_option": false}'),
(4, 'Database Administrator','Full-time',  80000, 100000, 'https://www.healthbridge.example/jobs/5','2026-11-01',
 '{"required_skills": ["SQL","MySQL","Linux","Backup & Recovery"], "preferred_skills": ["Python"], "education": "Bachelor in CS or IT", "experience_years": 2, "remote_option": false}'),
(5, 'Machine Learning Engineer', 'Full-time', 100000, 130000, 'https://www.brightpath.example/jobs/6','2026-11-03',
 '{"required_skills": ["Python","TensorFlow","SQL","Statistics"], "preferred_skills": ["AWS"], "education": "Bachelor or Master in CS", "experience_years": 2, "remote_option": true}'),
(4, 'Full-Stack Developer','Contract',   70000,  90000, 'https://www.healthbridge.example/jobs/7','2026-11-05',
 '{"required_skills": ["JavaScript","Python","Flask","HTML","CSS"], "preferred_skills": ["React"], "education": "Bachelor degree", "experience_years": 2, "remote_option": true}'),
(2, 'QA Tester','Part-time',  25000,  35000, 'https://www.dataco.example/jobs/8',    '2026-11-08',
 '{"required_skills": ["Testing","Git","SQL"], "preferred_skills": [], "education": "High school diploma or higher", "experience_years": 0, "remote_option": false}');

INSERT INTO applications (job_id, application_date, status, resume_version, cover_letter_sent, interview_data) VALUES
(1, '2026-10-14', 'Interview', 'v2-tech', TRUE,'{"interview_rounds": 2, "interviewers": ["Sarah Johnson","Mike Chen"], "technical_questions": ["SQL joins","Python basics","API design"], "feedback": "Strong technical skills, good communication", "next_steps": "Final round scheduled"}'),
(2, '2026-10-16', 'Applied',   'v2-data', FALSE, NULL),
(3, '2026-10-22', 'Screening', 'v2-tech', TRUE, NULL),
(5, '2026-11-02', 'Offer',     'v3-dba',  TRUE,'{"interview_rounds": 3, "interviewers": ["Emily Williams"], "technical_questions": ["Database normalization","Transaction isolation"], "feedback": "Excellent fundamentals", "next_steps": "Review offer letter", "offer_amount": 92000}'),
(6, '2026-11-04', 'Rejected',  'v3-ml',   TRUE,'{"interview_rounds": 1, "interviewers": ["David Brown"], "feedback": "Needs more ML project experience"}'),
(4, '2026-10-27', 'Withdrawn', 'v2-tech', FALSE, NULL);

INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes) VALUES
(1, 'Sarah Johnson','Engineering Manager', 'sarah.johnson@techcorp.example', '305-555-0101', 'https://www.linkedin.com/in/sarah-johnson-example', 'Led the first interview'),
(1, 'Mike Chen','Senior Developer','mike.chen@techcorp.example','305-555-0102', NULL, NULL),
(2, 'Priya Patel','Recruiter','priya.patel@dataco.example','512-555-0110', 'https://www.linkedin.com/in/priya-patel-example', 'Prefers email'),
(3, 'Tom Alvarez','Talent Partner', 'tom.alvarez@cloudnine.example', '206-555-0120', NULL, NULL),
(4, 'Emily Williams', 'IT Director','emily.williams@healthbridge.example', '813-555-0130', NULL, 'Sent the offer details'),
(5, 'David Brown','CTO','david.brown@brightpath.example', '407-555-0140', NULL, 'Follow up in January');

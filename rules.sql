-- ============================================================================
-- DATABASE SCHEMA
-- ============================================================================
-- create database rules;
-- use rules;

CREATE TABLE regulations (
    regulation_id VARCHAR(10) PRIMARY KEY,
    regulation_name VARCHAR(200),
    jurisdiction VARCHAR(100),
    official_source TEXT,
    effective_date DATE,
    last_amended DATE
);

CREATE TABLE compliance_rules (
    rule_id VARCHAR(20) PRIMARY KEY,
    regulation_id VARCHAR(10),
    section_citation VARCHAR(50),
    rule_title VARCHAR(300),
    rule_text TEXT,
    violation_penalty_min DECIMAL(15,2),
    violation_penalty_max DECIMAL(15,2),
    applies_to VARCHAR(100),
    FOREIGN KEY (regulation_id) REFERENCES regulations(regulation_id)
);

-- ============================================================================
-- REGULATIONS METADATA
-- ============================================================================

INSERT INTO regulations VALUES 
('CCPA', 'California Consumer Privacy Act (as amended by CPRA)', 'California, United States',
'California Civil Code §1798.100-1798.199.100 | Official Source: https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&lawCode=CIV&title=1.81.5',
'2020-01-01', '2023-01-01'),

('GDPR', 'General Data Protection Regulation', 'European Union',
'Regulation (EU) 2016/679 | Official Source: https://eur-lex.europa.eu/eli/reg/2016/679/oj',
'2018-05-25', '2018-05-25');

-- ============================================================================
-- CCPA OFFICIAL RULES
-- Source: California Civil Code §1798.100-1798.199.100
-- Official URL: https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&lawCode=CIV&title=1.81.5
-- ============================================================================

-- Section 1798.120 - Right to Opt-Out of Sale/Sharing
INSERT INTO compliance_rules VALUES 
('CCPA-1798.120', 'CCPA', '§1798.120(a)', 
'Right to Opt-Out of Sale or Sharing of Personal Information',
'A consumer shall have the right, at any time, to direct a business that sells or shares personal information about the consumer to third parties not to sell or share the consumer''s personal information. This right may be referred to as the right to opt-out of sale or sharing.',
2500.00, 7500.00, 'All businesses that sell or share personal information');

-- Section 1798.135 - Methods for Submitting Opt-Out Requests
INSERT INTO compliance_rules VALUES 
('CCPA-1798.135a', 'CCPA', '§1798.135(a)', 
'Provide Clear and Conspicuous Link to Opt-Out',
'A business that is required to comply with Section 1798.120 shall, in a form that is reasonably accessible to consumers: (1) Provide a clear and conspicuous link on the business''s Internet homepage(s), titled "Do Not Sell or Share My Personal Information," to an Internet Web page that enables a consumer, or a person authorized by the consumer, to opt-out of the sale or sharing of the consumer''s personal information.',
2500.00, 7500.00, 'Businesses selling or sharing personal information');

INSERT INTO compliance_rules VALUES 
('CCPA-1798.135b', 'CCPA', '§1798.135(b)(1)', 
'Honor Opt-Out Preference Signals (Global Privacy Control)',
'A business that collects personal information from consumers online shall: (1) Treat user-enabled global privacy controls, such as a browser plugin or privacy setting, device setting, or other mechanism, that communicate or signal the consumer''s choice to opt-out of the sale or sharing of their personal information as a valid request submitted pursuant to Section 1798.120 for that browser or device, or, if known, for the consumer.',
2500.00, 7500.00, 'All businesses collecting information online');

-- Section 1798.121 - Right to Limit Sensitive Personal Information
INSERT INTO compliance_rules VALUES 
('CCPA-1798.121', 'CCPA', '§1798.121(a)', 
'Right to Limit Use and Disclosure of Sensitive Personal Information',
'A consumer shall have the right, at any time, to direct a business that collects sensitive personal information about the consumer to limit its use of the consumer''s sensitive personal information to that use which is necessary to perform the services or provide the goods reasonably expected by an average consumer who requests those goods or services.',
2500.00, 7500.00, 'Businesses collecting sensitive personal information');

-- Section 1798.100 - Right to Know
INSERT INTO compliance_rules VALUES 
('CCPA-1798.100', 'CCPA', '§1798.100(a)', 
'Right to Know What Personal Information is Collected',
'A consumer shall have the right to request that a business that collects personal information about the consumer disclose to the consumer the following: (1) The categories of personal information it has collected about that consumer. (2) The categories of sources from which the personal information is collected. (3) The business or commercial purpose for collecting, selling, or sharing personal information. (4) The categories of third parties to whom the business discloses personal information. (5) The specific pieces of personal information it has collected about that consumer.',
2500.00, 7500.00, 'All businesses collecting personal information');

-- Section 1798.105 - Right to Delete
INSERT INTO compliance_rules VALUES 
('CCPA-1798.105', 'CCPA', '§1798.105(a)', 
'Right to Delete Personal Information',
'A consumer shall have the right to request that a business delete any personal information about the consumer which the business has collected from the consumer.',
2500.00, 7500.00, 'All businesses collecting personal information');

INSERT INTO compliance_rules VALUES 
('CCPA-1798.105c', 'CCPA', '§1798.105(c)', 
'Business Must Delete and Direct Service Providers to Delete',
'A business that receives a verifiable consumer request from a consumer to delete the consumer''s personal information pursuant to subdivision (a) shall delete the consumer''s personal information from its records, notify any service providers or contractors to delete the consumer''s personal information from their records, and notify all third parties to whom the business has sold or shared the consumer''s personal information to delete the consumer''s personal information unless this proves impossible or involves disproportionate effort.',
2500.00, 7500.00, 'All businesses with service providers');

-- Section 1798.125 - Non-Discrimination
INSERT INTO compliance_rules VALUES 
('CCPA-1798.125a', 'CCPA', '§1798.125(a)(1)', 
'Prohibition on Discriminating Against Consumers',
'A business shall not discriminate against a consumer because the consumer exercised any of the consumer''s rights under this title, including, but not limited to, by: (1) Denying goods or services to the consumer. (2) Charging different prices or rates for goods or services, including through the use of discounts or other benefits or imposing penalties. (3) Providing a different level or quality of goods or services to the consumer. (4) Suggesting that the consumer will receive a different price or rate for goods or services or a different level or quality of goods or services.',
2500.00, 7500.00, 'All businesses subject to CCPA');

-- Section 1798.130 - Notice Requirements
INSERT INTO compliance_rules VALUES 
('CCPA-1798.130a5A', 'CCPA', '§1798.130(a)(5)(A)', 
'Privacy Policy Must Describe Consumer Rights',
'A business shall, in its online privacy policy or policies and in any California-specific description of consumers'' privacy rights, describe the consumer''s rights under Sections 1798.100, 1798.105, 1798.110, 1798.115, 1798.120, and 1798.121.',
2500.00, 7500.00, 'All businesses with online presence');

-- Section 1798.140 - Definitions: Sale
INSERT INTO compliance_rules VALUES 
('CCPA-1798.140ad', 'CCPA', '§1798.140(ad)(1)', 
'Definition of Sale of Personal Information',
'"Sale" means selling, renting, releasing, disclosing, disseminating, making available, transferring, or otherwise communicating orally, in writing, or by electronic or other means, a consumer''s personal information by the business to a third party for monetary or other valuable consideration.',
NULL, NULL, 'Definitional - applies to interpretation');

-- Section 1798.185 - Regulations (Processing Timeline)
INSERT INTO compliance_rules VALUES 
('CCPA-1798.185a14', 'CCPA', '§1798.185(a)(14)', 
'Opt-Out Must Be Processed Within 15 Business Days',
'A business shall comply with an opt-out request within 15 business days from the date the business receives the request.',
2500.00, 7500.00, 'All businesses receiving opt-out requests');

-- ============================================================================
-- GDPR OFFICIAL RULES
-- Source: Regulation (EU) 2016/679
-- Official URL: https://eur-lex.europa.eu/eli/reg/2016/679/oj
-- ============================================================================

-- Article 6 - Lawfulness of Processing
INSERT INTO compliance_rules VALUES 
('GDPR-Art6.1', 'GDPR', 'Article 6(1)', 
'Processing Lawful Only If At Least One Legal Basis Applies',
'Processing shall be lawful only if and to the extent that at least one of the following applies: (a) the data subject has given consent to the processing of his or her personal data for one or more specific purposes; (b) processing is necessary for the performance of a contract; (c) processing is necessary for compliance with a legal obligation; (d) processing is necessary to protect vital interests; (e) processing is necessary for public interest or official authority; (f) processing is necessary for legitimate interests pursued by the controller or by a third party.',
10000000.00, 20000000.00, 'All data controllers and processors');

-- Article 7 - Conditions for Consent
INSERT INTO compliance_rules VALUES 
('GDPR-Art7.1', 'GDPR', 'Article 7(1)', 
'Controller Must Demonstrate Consent Was Given',
'Where processing is based on consent, the controller shall be able to demonstrate that the data subject has consented to processing of his or her personal data.',
10000000.00, 20000000.00, 'All controllers relying on consent');

INSERT INTO compliance_rules VALUES 
('GDPR-Art7.2', 'GDPR', 'Article 7(2)', 
'Consent Request Must Be Clearly Distinguishable',
'If the data subject''s consent is given in the context of a written declaration which also concerns other matters, the request for consent shall be presented in a manner which is clearly distinguishable from the other matters, in an intelligible and easily accessible form, using clear and plain language.',
10000000.00, 20000000.00, 'All controllers obtaining written consent');

INSERT INTO compliance_rules VALUES 
('GDPR-Art7.3', 'GDPR', 'Article 7(3)', 
'Right to Withdraw Consent at Any Time',
'The data subject shall have the right to withdraw his or her consent at any time. The withdrawal of consent shall not affect the lawfulness of processing based on consent before its withdrawal. It shall be as easy to withdraw as to give consent.',
10000000.00, 20000000.00, 'All controllers relying on consent');

INSERT INTO compliance_rules VALUES 
('GDPR-Art7.4', 'GDPR', 'Article 7(4)', 
'Consent Not Valid If Service Conditional on Unnecessary Processing',
'When assessing whether consent is freely given, utmost account shall be taken of whether, inter alia, the performance of a contract, including the provision of a service, is conditional on consent to the processing of personal data that is not necessary for the performance of that contract.',
10000000.00, 20000000.00, 'All controllers using consent as legal basis');

-- Article 5 - Principles
INSERT INTO compliance_rules VALUES 
('GDPR-Art5.1a', 'GDPR', 'Article 5(1)(a)', 
'Lawfulness, Fairness and Transparency',
'Personal data shall be processed lawfully, fairly and in a transparent manner in relation to the data subject.',
10000000.00, 20000000.00, 'All data controllers');

INSERT INTO compliance_rules VALUES 
('GDPR-Art5.1b', 'GDPR', 'Article 5(1)(b)', 
'Purpose Limitation',
'Personal data shall be collected for specified, explicit and legitimate purposes and not further processed in a manner that is incompatible with those purposes.',
10000000.00, 20000000.00, 'All data controllers');

INSERT INTO compliance_rules VALUES 
('GDPR-Art5.1c', 'GDPR', 'Article 5(1)(c)', 
'Data Minimization',
'Personal data shall be adequate, relevant and limited to what is necessary in relation to the purposes for which they are processed.',
10000000.00, 20000000.00, 'All data controllers');

INSERT INTO compliance_rules VALUES 
('GDPR-Art5.1d', 'GDPR', 'Article 5(1)(d)', 
'Accuracy',
'Personal data shall be accurate and, where necessary, kept up to date; every reasonable step must be taken to ensure that personal data that are inaccurate are erased or rectified without delay.',
10000000.00, 20000000.00, 'All data controllers');

INSERT INTO compliance_rules VALUES 
('GDPR-Art5.1e', 'GDPR', 'Article 5(1)(e)', 
'Storage Limitation',
'Personal data shall be kept in a form which permits identification of data subjects for no longer than is necessary for the purposes for which the personal data are processed.',
10000000.00, 20000000.00, 'All data controllers');

INSERT INTO compliance_rules VALUES 
('GDPR-Art5.1f', 'GDPR', 'Article 5(1)(f)', 
'Integrity and Confidentiality',
'Personal data shall be processed in a manner that ensures appropriate security of the personal data, including protection against unauthorized or unlawful processing and against accidental loss, destruction or damage, using appropriate technical or organizational measures.',
10000000.00, 20000000.00, 'All data controllers');

-- Article 13 - Information to Be Provided (Transparency)
INSERT INTO compliance_rules VALUES 
('GDPR-Art13.1', 'GDPR', 'Article 13(1)', 
'Provide Information at Time of Collection',
'Where personal data relating to a data subject are collected from the data subject, the controller shall, at the time when personal data are obtained, provide the data subject with: identity of controller, contact details of DPO, purposes and legal basis, legitimate interests, recipients of data, international transfers, retention period, rights of data subject, right to withdraw consent, right to lodge complaint, whether requirement is statutory or contractual, and existence of automated decision-making.',
10000000.00, 20000000.00, 'All data controllers collecting directly from individuals');

-- Article 17 - Right to Erasure
INSERT INTO compliance_rules VALUES 
('GDPR-Art17.1', 'GDPR', 'Article 17(1)', 
'Right to Erasure (Right to Be Forgotten)',
'The data subject shall have the right to obtain from the controller the erasure of personal data concerning him or her without undue delay and the controller shall have the obligation to erase personal data without undue delay where one of the following grounds applies: (a) data no longer necessary; (b) consent withdrawn; (c) objection to processing; (d) unlawful processing; (e) legal obligation to erase; (f) data collected in relation to information society services offered to children.',
10000000.00, 20000000.00, 'All data controllers');

-- Article 21 - Right to Object
INSERT INTO compliance_rules VALUES 
('GDPR-Art21.1', 'GDPR', 'Article 21(1)', 
'Right to Object to Processing',
'The data subject shall have the right to object, on grounds relating to his or her particular situation, at any time to processing of personal data concerning him or her which is based on point (e) or (f) of Article 6(1), including profiling based on those provisions. The controller shall no longer process the personal data unless the controller demonstrates compelling legitimate grounds for the processing which override the interests, rights and freedoms of the data subject.',
10000000.00, 20000000.00, 'Controllers using legitimate interest or public interest basis');

INSERT INTO compliance_rules VALUES 
('GDPR-Art21.2', 'GDPR', 'Article 21(2)', 
'Absolute Right to Object to Direct Marketing',
'Where personal data are processed for direct marketing purposes, the data subject shall have the right to object at any time to processing of personal data concerning him or her for such marketing, which includes profiling to the extent that it is related to such direct marketing.',
10000000.00, 20000000.00, 'Controllers processing for direct marketing');

INSERT INTO compliance_rules VALUES 
('GDPR-Art21.3', 'GDPR', 'Article 21(3)', 
'Right to Object Must Be Explicitly Brought to Attention',
'Where the data subject objects to processing for direct marketing purposes, the personal data shall no longer be processed for such purposes.',
10000000.00, 20000000.00, 'Controllers processing for direct marketing');

INSERT INTO compliance_rules VALUES 
('GDPR-Art21.5', 'GDPR', 'Article 21(5)', 
'Right to Object in Context of Information Society Services',
'In the context of the use of information society services, and notwithstanding Directive 2002/58/EC, the data subject may exercise his or her right to object by automated means using technical specifications.',
10000000.00, 20000000.00, 'Online service providers');

-- Article 22 - Automated Decision-Making
INSERT INTO compliance_rules VALUES 
('GDPR-Art22.1', 'GDPR', 'Article 22(1)', 
'Right Not to Be Subject to Automated Decision-Making',
'The data subject shall have the right not to be subject to a decision based solely on automated processing, including profiling, which produces legal effects concerning him or her or similarly significantly affects him or her.',
10000000.00, 20000000.00, 'Controllers using automated decision-making');

-- Article 44 - International Transfers
INSERT INTO compliance_rules VALUES 
('GDPR-Art44', 'GDPR', 'Article 44', 
'General Principle for International Transfers',
'Any transfer of personal data which are undergoing processing or are intended for processing after transfer to a third country or to an international organization shall take place only if the conditions laid down in this Chapter are complied with by the controller and processor, including for onward transfers of personal data from the third country or an international organization to another third country or to another international organization.',
10000000.00, 20000000.00, 'Controllers and processors transferring data outside EU');

-- Article 83 - Administrative Fines
INSERT INTO compliance_rules VALUES 
('GDPR-Art83.5', 'GDPR', 'Article 83(5)', 
'Maximum Administrative Fines for Serious Infringements',
'Infringements of basic principles for processing (Article 5, 6, 7, 9), data subjects rights (Article 12-22), transfers to third countries (Article 44-49) shall be subject to administrative fines up to EUR 20,000,000, or in case of an undertaking, up to 4% of total worldwide annual turnover of preceding financial year, whichever is higher.',
10000000.00, 20000000.00, 'All controllers and processors - serious violations');

INSERT INTO compliance_rules VALUES 
('GDPR-Art83.4', 'GDPR', 'Article 83(4)', 
'Administrative Fines for Other Infringements',
'Infringements of controller/processor obligations (Article 8, 11, 25-39, 42, 43), certification body obligations (Article 42, 43), monitoring body obligations (Article 41(4)) shall be subject to administrative fines up to EUR 10,000,000, or in case of an undertaking, up to 2% of total worldwide annual turnover of preceding financial year, whichever is higher.',
5000000.00, 10000000.00, 'All controllers and processors - other violations');

-- ePrivacy Directive (Cookie Consent)
INSERT INTO compliance_rules VALUES 
('GDPR-ePD-Art5.3', 'GDPR', 'ePrivacy Directive Article 5(3)', 
'Prior Consent Required for Storing Information on User Device',
'The storing of information, or the gaining of access to information already stored, in the terminal equipment of a subscriber or user is only allowed on condition that the subscriber or user concerned has given his or her consent, having been provided with clear and comprehensive information, in accordance with Directive 95/46/EC, inter alia, about the purposes of the processing. This shall not prevent any technical storage or access for the sole purpose of carrying out the transmission of a communication over an electronic communications network, or as strictly necessary in order for the provider of an information society service explicitly requested by the subscriber or user to provide the service.',
NULL, NULL, 'All websites using cookies or similar technologies');

select * from compliance_rules;
select count(*) from compliance_rules;
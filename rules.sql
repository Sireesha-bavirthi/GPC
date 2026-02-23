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
-- CCPA + CPRA RULES (COMBINED — ONE AMENDED LAW)
-- Source: California Civil Code §1798.100-1798.199.100
-- CPRA effective: January 1, 2023
-- Official URL: https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&lawCode=CIV&title=1.81.5
-- CPPA Regulations: https://cppa.ca.gov/regulations/
-- ============================================================================

-- -----------------------------------------------------------------------
-- ORIGINAL CCPA RULES (still fully valid, unchanged)
-- -----------------------------------------------------------------------

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
'A consumer shall have the right, at any time, to direct a business that collects sensitive personal information about the consumer to limit its use of the consumer''s sensitive personal information to that use which is necessary to perform the services or provide the goods reasonably expected by an average consumer who requests those goods or services. Sensitive personal information includes: social security number, driver''s license, state ID or passport number; account log-in credentials; financial account information; precise geolocation; racial or ethnic origin; religious beliefs; union membership; contents of communications; genetic data; biometric data; health data; sex life or sexual orientation data; and personal information of consumers known to be under 16 years old.',
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
'A business shall, in its online privacy policy or policies and in any California-specific description of consumers'' privacy rights, describe the consumer''s rights under Sections 1798.100, 1798.105, 1798.106, 1798.110, 1798.115, 1798.120, and 1798.121, and provide two or more designated methods for submitting requests including at minimum a toll-free telephone number.',
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


-- -----------------------------------------------------------------------
-- NEW CPRA RULES (added by CPRA, effective January 1, 2023)
-- -----------------------------------------------------------------------

-- Section 1798.106 - NEW: Right to Correct (CPRA addition)
INSERT INTO compliance_rules VALUES 
('CCPA-1798.106', 'CCPA', '§1798.106(a)', 
'Right to Correct Inaccurate Personal Information',
'A consumer shall have the right to request a business that maintains inaccurate personal information about the consumer to correct that inaccurate personal information, taking into account the nature of the personal information and the purposes of the processing of the personal information. A business that collects personal information about consumers shall disclose the consumer''s right to request correction of inaccurate personal information. Upon receiving a verifiable consumer request, a business shall use commercially reasonable efforts to correct the inaccurate personal information within 45 days.',
2500.00, 7500.00, 'All businesses collecting personal information');

-- Section 1798.120 - NEW: Right to Opt-Out of SHARING (cross-context behavioral advertising — CPRA addition)
INSERT INTO compliance_rules VALUES 
('CCPA-1798.120b', 'CCPA', '§1798.120(a) + §1798.140(ah)', 
'Right to Opt-Out of Sharing for Cross-Context Behavioral Advertising',
'CPRA expanded the right to opt-out to cover not just "sale" of personal information but also "sharing," defined as disclosing, making available, or transferring a consumer''s personal information to a third party for cross-context behavioral advertising, whether or not for monetary or other valuable consideration. Businesses must honor opt-out requests for sharing just as they honor opt-out requests for sale. The "Do Not Sell or Share My Personal Information" link must cover both.',
2500.00, 7500.00, 'All businesses sharing data for behavioral advertising');

-- Section 1798.135(c) - NEW: "Limit the Use of My Sensitive Personal Information" Link Required
INSERT INTO compliance_rules VALUES 
('CCPA-1798.135c', 'CCPA', '§1798.135(c)', 
'Must Provide "Limit the Use of My Sensitive Personal Information" Link',
'A business that uses or discloses a consumer''s sensitive personal information for purposes other than those authorized by Section 1798.121(a) shall provide a clear and conspicuous link on the business''s homepage titled "Limit the Use of My Sensitive Personal Information" that enables consumers to exercise their right to limit such use. This link may be combined with the "Do Not Sell or Share" link if clearly labeled.',
2500.00, 7500.00, 'Businesses using sensitive personal information beyond authorized purposes');

-- Section 1798.100(a)(3) - NEW: Data Minimization and Retention Limits (CPRA addition)
INSERT INTO compliance_rules VALUES 
('CCPA-1798.100a3', 'CCPA', '§1798.100(a)(3)', 
'Data Collection Must Be Reasonably Necessary and Proportionate — Data Minimization',
'A business''s collection, use, retention, and sharing of a consumer''s personal information shall be reasonably necessary and proportionate to achieve the purposes for which the personal information was collected or processed, or for another disclosed purpose that is compatible with the context in which the personal information was collected, and not further processed in a manner incompatible with those purposes.',
2500.00, 7500.00, 'All businesses collecting personal information');

-- Section 1798.100(a)(1) — NEW: Retention Period Disclosure Required (CPRA addition)
INSERT INTO compliance_rules VALUES 
('CCPA-1798.100a1', 'CCPA', '§1798.100(a)(1)', 
'Must Disclose Retention Period for Each Category of Personal Information',
'At or before the point of collection, a business shall inform consumers of the length of time the business intends to retain each category of personal information collected, including sensitive personal information, or if it is not possible to provide a specific timeframe, the criteria used to determine the retention period. Personal information shall not be retained longer than is reasonably necessary for the disclosed purpose.',
2500.00, 7500.00, 'All businesses collecting personal information');

-- Section 1798.150 - NEW: Private Right of Action for Data Breaches includes additional data types
INSERT INTO compliance_rules VALUES 
('CCPA-1798.150', 'CCPA', '§1798.150(a)', 
'Private Right of Action for Unauthorized Disclosure of Personal Information',
'Any consumer whose nonencrypted or nonredacted personal information, including email address in combination with a password or security question and answer that would permit access to the account, is subject to an unauthorized access, exfiltration, theft, or disclosure as a result of the business''s violation of the duty to implement and maintain reasonable security procedures and practices may bring a civil action for statutory damages between $100 and $750 per consumer per incident, or actual damages, whichever is greater.',
100.00, 750.00, 'All businesses holding consumer personal information');

-- Section 1798.199.90 - NEW: No 30-Day Cure Period (CPRA eliminated it)
INSERT INTO compliance_rules VALUES 
('CCPA-1798.199.90', 'CCPA', '§1798.199.90', 
'No Automatic 30-Day Cure Period for Violations',
'The California Privacy Protection Agency (CPPA) has full discretion on whether to offer a cure period before issuing fines. Unlike the original CCPA which required a mandatory 30-day cure period before any enforcement action could be taken, the CPRA eliminated this automatic cure period effective January 1, 2023. The Agency may consider a cure period at its discretion but is not required to provide one.',
2500.00, 7500.00, 'All businesses subject to CCPA enforcement');

-- Section 1798.140(ae) - NEW: Sensitive Personal Information Full Definition (CPRA addition)
INSERT INTO compliance_rules VALUES 
('CCPA-1798.140ae', 'CCPA', '§1798.140(ae)', 
'Definition of Sensitive Personal Information — Complete CPRA Categories',
'"Sensitive personal information" means personal information that reveals: (1) Social security, driver''s license, state identification card, or passport number; (2) Account log-in credentials (username/email + password or security question); (3) Financial account number, debit/credit card number in combination with access code; (4) Precise geolocation (within 1,850 feet radius); (5) Racial or ethnic origin, religious or philosophical beliefs, or union membership; (6) Contents of consumer''s mail, email, and text messages unless the business is the intended recipient; (7) Genetic data; (8) Biometric information processed to uniquely identify a consumer; (9) Personal information collected and analyzed concerning a consumer''s health; (10) Personal information collected and analyzed concerning a consumer''s sex life or sexual orientation; (11) Personal information of consumers known to be under 16 years old.',
2500.00, 7500.00, 'All businesses collecting sensitive personal information');

-- Section 1798.140(ae) - NEW: Definition of "Sharing" (cross-context behavioral advertising)
INSERT INTO compliance_rules VALUES 
('CCPA-1798.140ah', 'CCPA', '§1798.140(ah)', 
'Definition of Sharing of Personal Information',
'"Share," "shared," or "sharing" means sharing, renting, releasing, disclosing, disseminating, making available, transferring, or otherwise communicating orally, in writing, or by electronic or other means, a consumer''s personal information by the business to a third party for cross-context behavioral advertising, whether or not for monetary or other valuable consideration, including transactions between a business and a third party for cross-context behavioral advertising for the benefit of a business in which no money is exchanged.',
NULL, NULL, 'Definitional — applies to all businesses sharing data for advertising');

-- Section 1798.185(a)(15) — NEW: Cybersecurity Audit Requirement (effective January 1, 2026)
INSERT INTO compliance_rules VALUES 
('CCPA-1798.185a15', 'CCPA', '§1798.185(a)(15)', 
'Annual Cybersecurity Audit Required for High-Risk Businesses',
'Businesses whose processing of personal information presents significant risk to consumers'' privacy or security are required to conduct annual independent cybersecurity audits and submit risk assessments on a regular basis to the California Privacy Protection Agency. This applies to businesses that: derive 50% or more of annual revenues from selling or sharing personal information; or process personal information of 250,000 or more consumers. Effective January 1, 2026 per CPPA final regulations adopted July 24, 2025.',
2500.00, 7500.00, 'Businesses with high-risk data processing — effective January 1, 2026');

-- Section 1798.185(a)(16) — NEW: Risk Assessment Requirement (effective January 1, 2026)
INSERT INTO compliance_rules VALUES 
('CCPA-1798.185a16', 'CCPA', '§1798.185(a)(16)', 
'Privacy Risk Assessment Required for High-Risk Processing Activities',
'Businesses that engage in processing activities that present a significant risk to consumers'' privacy or security must conduct and document risk assessments prior to undertaking such activities. High-risk processing includes: selling or sharing personal information; processing sensitive personal information; processing personal information for targeted advertising or profiling; and using automated decision-making technology. Risk assessments must be submitted to the CPPA upon request. Effective January 1, 2026.',
2500.00, 7500.00, 'Businesses conducting high-risk processing activities — effective January 1, 2026');

-- Section 1798.185(a)(21) — NEW: Automated Decision-Making Technology (ADMT) Opt-Out Right
INSERT INTO compliance_rules VALUES 
('CCPA-1798.185a21', 'CCPA', '§1798.185(a)(21)', 
'Right to Opt-Out of Automated Decision-Making Technology (ADMT)',
'Businesses using automated decision-making technology (ADMT) — including AI and profiling systems — for decisions that produce legal or similarly significant effects concerning consumers in areas such as education, employment, housing, credit, healthcare, or insurance must: (1) Provide a "pre-use notice" informing consumers before ADMT is applied to them; (2) Allow consumers to opt-out of ADMT for significant decisions; (3) Upon request, provide a plain-language explanation of how the ADMT works and the basis for any decision made. Effective January 1, 2026 per CPPA final regulations.',
2500.00, 7500.00, 'Businesses using AI or automated decision-making — effective January 1, 2026');

-- Section 1798.199.90 penalties — Children's Data Higher Penalty
INSERT INTO compliance_rules VALUES 
('CCPA-1798.199.90b', 'CCPA', '§1798.199.90(b)', 
'Tripled Penalties for Violations Involving Personal Information of Minors Under 16',
'Any intentional violation of the CCPA, or any violation involving the personal information of consumers known to be under 16 years of age, is subject to a civil penalty of up to $7,500 per violation. Each consumer whose rights are violated may give rise to a separate violation. There is no automatic cure period for violations involving minors.',
7500.00, 7500.00, 'All businesses — mandatory higher penalty for children''s data violations');

-- Section 1798.135(b)(2) — NEW: GPC Opt-Out Confirmation Required
INSERT INTO compliance_rules VALUES 
('CCPA-1798.135b2', 'CCPA', '§1798.135(b)(2)', 
'Must Confirm That GPC Opt-Out Signal Has Been Processed',
'When a business receives a valid Global Privacy Control (GPC) opt-out signal, it must not only honor the request but must be capable of confirming to consumers that their opt-out preference has been recognized and processed. A business shall not require a consumer to create an account in order to make a verifiable consumer request or to have their GPC signal honored.',
2500.00, 7500.00, 'All businesses collecting personal information online');

-- Section 1798.115 — Right to Know What Personal Information is SOLD or SHARED and to Whom
INSERT INTO compliance_rules VALUES 
('CCPA-1798.115', 'CCPA', '§1798.115(a)', 
'Right to Know What Personal Information is Sold or Shared and to Whom',
'A consumer shall have the right to request that a business that sells or shares the consumer''s personal information, or that discloses it for a business purpose, disclose to that consumer: (1) The categories of personal information that the business collected about the consumer. (2) The categories of personal information that the business sold or shared about the consumer and the categories of third parties to whom the personal information was sold or shared, by category or categories of personal information for each category of third parties to whom the personal information was sold or shared. (3) The categories of personal information that the business disclosed about the consumer for a business purpose and the categories of persons to whom it was disclosed for a business purpose.',
2500.00, 7500.00, 'All businesses that sell or share personal information');

-- Section 1798.110 — Right to Access (full access right including portable format)
INSERT INTO compliance_rules VALUES 
('CCPA-1798.110', 'CCPA', '§1798.110(a)', 
'Right to Access Personal Information in Portable Format',
'A consumer shall have the right to request that a business that collects personal information about the consumer disclose to the consumer, free of charge: the categories and specific pieces of personal information the business has collected, the sources, the business or commercial purpose, and the third parties. If the consumer''s request is made electronically, the business shall provide the information in a portable and, to the extent technically feasible, readily useable format that allows the consumer to transmit this information to another entity without hindrance.',
2500.00, 7500.00, 'All businesses collecting personal information');

-- Data Broker Registry (SB 362, signed October 2023 — operative January 1, 2024)
INSERT INTO compliance_rules VALUES 
('CCPA-SB362', 'CCPA', 'Civil Code §1798.99.80 (SB 362)', 
'Data Brokers Must Register and Honor Single Deletion Request',
'All data brokers must annually register with the California Privacy Protection Agency and pay a registration fee. By January 1, 2026, the CPPA shall establish a single "Delete Request" mechanism enabling consumers to submit one request to delete their personal information from ALL registered data brokers simultaneously. Data brokers that fail to register or comply with deletion requests are subject to civil penalties. A "data broker" means a business that knowingly collects and sells to third parties the personal information of a consumer with whom the business does not have a direct relationship.',
200.00, 7500.00, 'All businesses that qualify as data brokers under SB 362');


-- ============================================================================
-- GDPR OFFICIAL RULES (unchanged — still fully valid)
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


-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

SELECT 
    regulation_id,
    COUNT(*) AS total_rules
FROM compliance_rules
GROUP BY regulation_id;

SELECT * FROM compliance_rules ORDER BY regulation_id, rule_id;

SELECT COUNT(*) AS grand_total FROM compliance_rules;

-- Expected output:
-- CCPA: ~21 rules (10 original + 11 new CPRA additions)
-- GDPR: 19 rules (unchanged)
-- Grand total: ~40 rules
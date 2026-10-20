"""Seed regulatory corpus for India mortgage underwriting pilot (Lucknow / UP).

Implements Playbook Section 14.1 (India counterpart):
- RBI KFS & Fair Practices Code
- RERA Act 2016 & UP-RERA Rules
- SARFAESI Act 2002 & CERSAI
- RBI KYC Master Direction
- RBI Housing Loan LTV Prudential Norms
- IBBI Registered Valuer appraisal standards
"""

from app.rag.ingestion import DocumentIngestionPipeline
from app.rag.schemas import RegDocument

CORPUS_DOCUMENTS = [
    {
        "meta": RegDocument(
            source_name="RBI Key Fact Statement Direction 2024",
            authority="Reserve Bank of India",
            category="kfs_apr",
            version_or_date="2024-04-15",
            scope="national",
            url="https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12658",
            sha256="rbi_kfs_2024_hash",
        ),
        "text": """
Section 3. Key Fact Statement (KFS) Requirements.
Regulated Entities (REs) must provide a Key Fact Statement (KFS) to all prospective borrowers in a standardized format before loan execution.
The KFS must prominently disclose:
(a) Loan amount, term, and interest rate type (fixed or floating).
(b) Annual Percentage Rate (APR) representing the total cost of credit including interest, processing charges, insurance, and valuation fees.
(c) Detailed repayment schedule displaying monthly EMI, principal component, and interest component.
(d) Explicit cooling-off or look-up period of at least 3 working days during which the borrower can exit without penalty.

Section 7. Penal Charges and Penal Interest.
Penalty, if charged for non-compliance with terms of the loan contract, shall be treated as 'penal charges' and shall not be levied in the form of 'penal interest' that is added to the rate of interest charged on the advances.
There shall be no capitalisation of penal charges, i.e., no interest shall be computed on penal charges.
The penal charges must be reasonable and proportionate to the non-compliance.
""",
    },
    {
        "meta": RegDocument(
            source_name="Real Estate (Regulation and Development) Act 2016",
            authority="Parliament of India",
            category="rera_act",
            version_or_date="2016-03-26",
            scope="national",
            url="https://www.indiacode.nic.in/handle/123456789/2158",
            sha256="rera_act_2016_hash",
        ),
        "text": """
Section 3. Prior Registration of Real Estate Project.
No promoter shall advertise, market, book, sell or offer for sale, or invite persons to purchase in any manner any plot, apartment or building in any real estate project, without registering the real estate project with the Real Estate Regulatory Authority established under this Act.
Provided that no such registration shall be required where the area of land proposed to be developed does not exceed five hundred square meters or the number of apartments proposed to be developed does not exceed eight.

Section 4. Application for Registration of Real Estate Projects.
Every promoter shall make an application to the Authority for registration of the real estate project in such form, manner, within such time and accompanied by such fee as may be specified by the regulations.
The promoter shall enclose an affidavit declaring that seventy percent of the amounts realised for the real estate project from the allottees, from time to time, shall be deposited in a separate account to be maintained in a scheduled bank to cover the cost of construction and the land cost and shall be used only for that purpose.
""",
    },
    {
        "meta": RegDocument(
            source_name="Uttar Pradesh Real Estate Rules 2016",
            authority="Government of Uttar Pradesh / UP-RERA",
            category="up_rera",
            version_or_date="2016-10-27",
            scope="state",
            state_code="UP",
            url="https://up-rera.in/rules",
            sha256="up_rera_rules_2016_hash",
        ),
        "text": """
Rule 4. Documents for Registration of Project in Uttar Pradesh.
The promoter shall submit an application to UP-RERA along with authenticated copy of the approvals and commencement certificate from the competent local authority (such as Lucknow Development Authority), sanctioned plan, layout plan and specifications of the proposed project.
Promoter shall disclose the status of title of the promoter to the land, along with non-encumbrance certificate from a legal practitioner.

Rule 10. Agreement for Sale and Allotment in Uttar Pradesh.
For the purpose of sub-section (2) of Section 13, the agreement for sale shall be in the form specified in Annexure A.
No promoter shall demand or accept more than ten percent of the cost of the apartment as an advance payment or an application fee without first entering into a written agreement for sale and registering the said agreement.
""",
    },
    {
        "meta": RegDocument(
            source_name="Maharashtra Real Estate Rules 2017",
            authority="Government of Maharashtra / MahaRERA",
            category="mh_rera",
            version_or_date="2017-05-08",
            scope="state",
            state_code="MH",
            url="https://maharera.maharashtra.gov.in/rules",
            sha256="mh_rera_rules_2017_hash",
        ),
        "text": """
Rule 3. Disclosure of Information by Promoters in Maharashtra.
Promoters in Maharashtra shall upload on the MahaRERA portal the legal title report, layout approvals, and details of encumbrances.
The promoter shall furnish a certificate from an engineer and architect certifying the percentage of completion.
""",
    },
    {
        "meta": RegDocument(
            source_name="SARFAESI Act 2002 and CERSAI Registry",
            authority="Parliament of India",
            category="sarfaesi_cersai",
            version_or_date="2002-12-17",
            scope="national",
            url="https://www.cersai.org.in",
            sha256="sarfaesi_cersai_hash",
        ),
        "text": """
Section 13. Enforcement of Security Interest.
Where any borrower, who is under a liability to a secured creditor under a security agreement, makes any default in repayment of secured debt, and his account in respect of such debt is classified by the secured creditor as non-performing asset, then, the secured creditor may require the borrower by notice in writing to discharge in full his liabilities within sixty days from the date of notice.

Section 26D. Right of Enforcement Conditional on CERSAI Registration.
Notwithstanding anything contained in this Act, no secured creditor shall be entitled to exercise the rights of enforcement of security interest under Chapter III unless the security interest over the property has been registered with the Central Registry (CERSAI).
All equitable mortgages, registered mortgages, and charges created over immovable property collateral must be filed in CERSAI within thirty days of creation.
""",
    },
    {
        "meta": RegDocument(
            source_name="RBI Master Direction - Know Your Customer 2016",
            authority="Reserve Bank of India",
            category="kyc_pmla",
            version_or_date="2016-02-25",
            scope="national",
            url="https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=11566",
            sha256="rbi_kyc_hash",
        ),
        "text": """
Section 16. Customer Due Diligence Procedure.
For undertaking Customer Due Diligence (CDD), the Regulated Entity shall obtain from an individual:
(a) One certified copy of an Officially Valid Document (OVD) containing details of identity and address (Passport, Driving Licence, Proof of possession of Aadhaar number, Voter's Identity Card).
(b) Permanent Account Number (PAN) or Form 60 as defined in the Income-tax Rules, 1962.
(c) One recent photograph.

Section 23. Central KYC Records Registry (CKYCR).
Regulated Entities shall capture the KYC information and upload the same onto the CKYCR portal within 10 days of the commencement of an account-based relationship with the customer.
""",
    },
    {
        "meta": RegDocument(
            source_name="RBI Housing Loans Prudential Norms on LTV Caps",
            authority="Reserve Bank of India",
            category="ltv_limits",
            version_or_date="2022-04-08",
            scope="national",
            url="https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12280",
            sha256="rbi_ltv_hash",
        ),
        "text": """
Paragraph 2. Loan to Value (LTV) Ratios for Housing Loans.
The maximum Loan to Value (LTV) ratio for individual housing loans granted by banks and housing finance companies shall be strictly capped as follows:
(a) For loan amounts up to Rs. 30 lakh: Maximum LTV ratio shall not exceed 90 percent.
(b) For loan amounts above Rs. 30 lakh and up to Rs. 75 lakh: Maximum LTV ratio shall not exceed 80 percent.
(c) For loan amounts above Rs. 75 lakh: Maximum LTV ratio shall not exceed 75 percent.
Risk weights on individual housing loans are tied to the LTV band and credit assessment.

Paragraph 4. Calculation of LTV Ratio.
The LTV ratio shall be calculated taking into account only the property purchase or construction cost as certified by an empanelled valuer or the agreement value, whichever is lower.
Stamp duty, registration charges and other documentation taxes shall not be included in the cost of the housing property for the purpose of calculating LTV.
""",
    },
    {
        "meta": RegDocument(
            source_name="IBBI Registered Valuers Rules 2017",
            authority="Insolvency and Bankruptcy Board of India",
            category="valuation_standards",
            version_or_date="2017-10-18",
            scope="national",
            url="https://www.ibbi.gov.in",
            sha256="ibbi_val_hash",
        ),
        "text": """
Rule 8. Conduct of Valuation and Independence.
The registered valuer shall conduct valuation in accordance with the valuation standards notified by the Central Government or International Valuation Standards (IVS).
The valuer shall maintain complete independence and shall not value any property collateral in which the valuer has any direct or indirect interest.
The valuation report shall disclose the purpose of valuation, date of inspection, methodology adopted (Comparable Sales Method or Cost Approach), and state any material divergence from government circle rates.
""",
    },
]


def load_seed_corpus(pipeline: DocumentIngestionPipeline) -> int:
    """Ingest the complete seed regulatory corpus into the pipeline vector store."""
    total_chunks = 0
    for doc in CORPUS_DOCUMENTS:
        chunks = pipeline.ingest_document_text(doc["meta"], doc["text"])
        total_chunks += len(chunks)
    return total_chunks

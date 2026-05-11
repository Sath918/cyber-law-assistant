import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def create_pdf(filename="Cyberlaw_dataset.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    Story = []

    title = "Information Technology Act, 2000 - Key Sections & Punishments"
    Story.append(Paragraph(title, styles['Title']))
    Story.append(Spacer(1, 12))

    sections = [
        {
            "section": "Section 65: Tampering with Computer Source Documents",
            "meaning": "Whoever knowingly or intentionally conceals, destroys or alters or intentionally or knowingly causes another to conceal, destroy, or alter any computer source code used for a computer, computer programme, computer system or computer network.",
            "punishment": "Imprisonment up to 3 years, or fine up to Rs 2 lakh, or both."
        },
        {
            "section": "Section 66: Computer Related Offences",
            "meaning": "If any person, dishonestly or fraudulently, does any act referred to in section 43 (damage to computer, computer system, etc), he shall be punishable.",
            "punishment": "Imprisonment up to 3 years or fine up to Rs 5 lakh or both."
        },
        {
            "section": "Section 66B: Stolen Computer Resource",
            "meaning": "Dishonestly receiving or retaining stolen computer resources or communication devices.",
            "punishment": "Imprisonment up to 3 years or fine up to Rs 1 lakh or both."
        },
        {
            "section": "Section 66C: Identity Theft",
            "meaning": "Fraudulently using electronic signatures, passwords, or unique identification features of others.",
            "punishment": "Imprisonment up to 3 years and fine up to Rs 1 lakh."
        },
        {
            "section": "Section 66D: Cheating by Personation",
            "meaning": "Cheating by personating someone using a communication device or computer resource.",
            "punishment": "Imprisonment up to 3 years and fine up to Rs 1 lakh."
        },
        {
            "section": "Section 66E: Violation of Privacy",
            "meaning": "Capturing or transmitting private images of a person without consent.",
            "punishment": "Imprisonment up to 3 years or fine up to Rs 2 lakh or both."
        },
        {
            "section": "Section 66F: Cyber Terrorism",
            "meaning": "Acts intended to threaten the unity, integrity, security, or sovereignty of India or strike terror in people using computer resources.",
            "punishment": "Imprisonment which may extend to imprisonment for life."
        },
        {
            "section": "Section 67: Obscene Material",
            "meaning": "Publishing or transmitting material which is lascivious or appeals to the prurient interest in electronic form.",
            "punishment": "First: Up to 3 years and fine up to Rs 5 lakh. Subsequent: Up to 5 years and fine up to Rs 10 lakh."
        },
        {
            "section": "Section 67A: Sexually Explicit Content",
            "meaning": "Publishing or transmitting material containing sexually explicit acts in electronic form.",
            "punishment": "First: Up to 5 years and fine up to Rs 10 lakh. Subsequent: Up to 7 years and fine up to Rs 10 lakh."
        },
        {
            "section": "Section 67B: Child Pornography",
            "meaning": "Publishing or transmitting material depicting children in sexually explicit acts in electronic form.",
            "punishment": "First: Up to 5 years and fine up to Rs 10 lakh. Subsequent: Up to 7 years and fine up to Rs 10 lakh."
        }
    ]

    Story.append(Paragraph("<b>Detailed Cyber Law Sections</b>", styles['Heading1']))
    for item in sections:
        Story.append(Paragraph(f"<b>{item['section']}</b>", styles['Heading2']))
        Story.append(Paragraph(f"<b>Meaning:</b> {item['meaning']}", styles['Normal']))
        Story.append(Paragraph(f"<b>Punishment:</b> {item['punishment']}", styles['Normal']))
        Story.append(Spacer(1, 10))

    Story.append(Spacer(1, 20))
    Story.append(Paragraph("<b>Awareness and Reporting Actions</b>", styles['Heading1']))
    awareness = [
        "<b>National Portal:</b> Report any cybercrime at <i>www.cybercrime.gov.in</i> immediately.",
        "<b>Helpline:</b> Call the National Cyber Crime Helpline number <b>1930</b> for immediate assistance, especially for financial frauds.",
        "<b>Financial Fraud:</b> If money is stolen, report within the first 'Golden Hour' (2 hours) to increase chances of recovery.",
        "<b>Evidence:</b> Keep screenshots, URLs, email headers, and transaction IDs as evidence for investigation."
    ]
    for tip in awareness:
        Story.append(Paragraph(tip, styles['Normal']))
        Story.append(Spacer(1, 8))

    Story.append(Spacer(1, 20))
    Story.append(Paragraph("<b>Recovery from Cyber Hacking</b>", styles['Heading1']))
    recovery = [
        "<b>Step 1: Secure Accounts.</b> Immediately change passwords for all compromised accounts using a different, clean device.",
        "<b>Step 2: Enable 2FA.</b> Turn on Two-Factor Authentication (2FA) wherever possible to prevent future unauthorized access.",
        "<b>Step 3: Scan Devices.</b> Run a full system scan with reputable antivirus software to remove any malware or keyloggers.",
        "<b>Step 4: Financial Freeze.</b> Contact your bank instantly to block cards and freeze accounts if financial data was exposed.",
        "<b>Step 5: Alert Contacts.</b> Inform friends and family that your account was hacked so they don't fall for scams sent from your profile.",
        "<b>Step 6: Official Report.</b> File a complaint on the National Cyber Crime portal (cybercrime.gov.in)."
    ]
    for step in recovery:
        Story.append(Paragraph(step, styles['Normal']))
        Story.append(Spacer(1, 8))

    doc.build(Story)
    print(f"{filename} created successfully.")

if __name__ == '__main__':
    create_pdf()

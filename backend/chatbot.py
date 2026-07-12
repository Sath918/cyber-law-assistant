def generate_response(message):
    message = message.lower()
    
    # Keyword-based dynamic responses for fallback mode
    if 'section 66' in message:
        return "Section 66 of the IT Act deals with computer-related offenses. It prescribes imprisonment up to 3 years or a fine up to 5 lakh rupees for dishonest acts involving computers. This includes unauthorized access and data tampering."
    
    elif 'whatsapp' in message or 'social media' in message:
        return "If your account is hacked, immediately: 1. Try to reset your password. 2. Log out of all other sessions. 3. Enable Two-Factor Authentication (2FA). 4. Inform your contacts to ignore any messages sent during the hack."
    
    elif 'protect' in message or 'security' in message:
        return "To protect yourself from cyber attacks: Use strong, unique passwords; enable Multi-Factor Authentication (MFA); avoid clicking suspicious links; and keep your software updated."
    
    elif 'report' in message or 'helpline' in message:
        return "You can report cybercrimes at www.cybercrime.gov.in or call the national helpline 1930. Keep screenshots and transaction IDs as evidence."
    
    elif 'hacking' in message or 'attack' in message:
        return "Cyber hacking is unauthorized access to a computer system. Under Section 66 of the IT Act, it's punishable by up to 3 years in prison. If you've been hacked, secure your accounts and report it to the authorities immediately."
    
    elif 'fraud' in message or 'scam' in message:
        return "Online fraud (like phishing or credit card scams) is punishable under Sections 66C and 66D. If you've lost money, contact your bank within 2 hours to increase chances of recovery."
    
    else:
        return "I am your AI Cyber Law Assistant. While I'm in basic mode, I can help with information about legal sections, account recovery, and reporting procedures. Try asking about 'Section 66', 'reporting a crime', or 'securing my account'."

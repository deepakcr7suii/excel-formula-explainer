import google.generativeai as genai

def setup_gemini(api_key):
    genai.configure(api_key=api_key)

def explain_formula(formula, cell_ref):
    """Send a formula to Gemini and get explanation + simplification in one call."""
    
    prompt = f"""You are an Excel formula expert. Analyze this formula:

Cell: {cell_ref}
Formula: {formula}

Respond in EXACTLY this format (no extra text):
EXPLANATION: [1-2 sentence plain English explanation of what this formula does]
SIMPLIFIED: [A simpler version of this formula if possible, or "No simplification needed" if it's already simple]"""

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Parse the response
        explanation = ""
        simplified = ""

        for line in text.split('\n'):
            if line.startswith('EXPLANATION:'):
                explanation = line.replace('EXPLANATION:', '').strip()
            elif line.startswith('SIMPLIFIED:'):
                simplified = line.replace('SIMPLIFIED:', '').strip()

        return {
            'explanation': explanation or 'Could not generate explanation.',
            'simplified': simplified or 'No simplification suggested.'
        }

    except Exception as e:
        return {
            'explanation': f'Error: {str(e)}',
            'simplified': 'N/A'
        }
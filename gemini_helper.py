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
        # Get the raw error text once, lowercase, for matching
        err_text = str(e).lower()

        # Quota / rate-limit errors (429)
        if '429' in err_text or 'quota' in err_text or 'rate' in err_text:
            return {
                'explanation': 'AI explanation temporarily unavailable — daily usage limit reached. Please try again later.',
                'simplified': 'Unavailable right now.'
            }

        # Auth errors (401 / 403) — bad or revoked API key
        if '401' in err_text or '403' in err_text or 'api key' in err_text or 'permission' in err_text:
            return {
                'explanation': 'AI explanation unavailable — service configuration issue.',
                'simplified': 'Unavailable right now.'
            }

        # Network / timeout errors
        if 'timeout' in err_text or 'connection' in err_text or 'network' in err_text:
            return {
                'explanation': 'AI explanation unavailable — connection issue. Please try again.',
                'simplified': 'Unavailable right now.'
            }

        # Everything else — generic fallback, never leak raw stack traces to users
        # Log to server console for debugging while showing clean message to user
        print(f'[Gemini error] cell={cell_ref} formula={formula[:50]} error={str(e)}')
        return {
            'explanation': 'AI explanation could not be generated for this formula.',
            'simplified': 'Unavailable right now.'
        }
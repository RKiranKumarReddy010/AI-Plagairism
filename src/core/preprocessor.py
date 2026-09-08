import re
import html
from typing import Optional


class TextPreprocessor:
    """Robust text preprocessor for cleaning raw document text, LaTeX, math symbols,

    unicode artifacts, and irregular punctuation while preserving linguistic integrity.
    """

    def __init__(self):
        self.latex_symbols = {
            r'$\sigma$': 'sigma', r'$\mu$': 'mu', r'$\alpha$': 'alpha',
            r'$\beta$': 'beta', r'$\gamma$': 'gamma', r'$\delta$': 'delta',
            r'$\epsilon$': 'epsilon', r'$\theta$': 'theta', r'$\lambda$': 'lambda',
            r'$\pi$': 'pi', r'$\omega$': 'omega', r'$\phi$': 'phi',
            r'\text{': '', r'\mathrm{': '', r'\mathbf{': '', r'\textbf{': '',
            r'\textit{': '', r'\frac{': '', r'\sqrt{': '', r'\sum': 'sum',
            r'\int': 'integral', r'\leq': 'less than or equal',
            r'\geq': 'greater than or equal', r'\neq': 'not equal',
            r'\approx': 'approximately', r'\pm': 'plus minus',
            r'\sigma': 'sigma', r'\mu': 'mu', r'\alpha': 'alpha',
            r'\beta': 'beta', r'\gamma': 'gamma', r'\delta': 'delta',
            r'\epsilon': 'epsilon', r'\theta': 'theta', r'\lambda': 'lambda',
            r'\pi': 'pi', r'\omega': 'omega', r'\phi': 'phi',
            r'\infty': 'infinity', r'\partial': 'partial',
            r'\nabla': 'nabla', r'\times': 'times', r'\div': 'divide', r'\cdot': 'dot',
            r'\rightarrow': 'approaches', r'\leftarrow': 'from',
            r'\Rightarrow': 'implies', r'\Leftarrow': 'implied by',
            r'\forall': 'for all', r'\exists': 'there exists',
            r'\in': 'in', r'\notin': 'not in', r'\subset': 'subset',
            r'\cup': 'union', r'\cap': 'intersection',
            r'\emptyset': 'empty set', r'\land': 'and', r'\lor': 'or',
            r'\neg': 'not', r'\implies': 'implies', r'\iff': 'if and only if',
        }

        self.math_replacements = {
            '∑': 'sum', '∏': 'product', '∫': 'integral', '∂': 'partial',
            '∇': 'nabla', '∞': 'infinity', '√': 'square root',
            '±': 'plus minus', '×': 'times', '÷': 'divide',
            '≤': 'less than or equal', '≥': 'greater than or equal',
            '≠': 'not equal', '≈': 'approximately', '≡': 'equivalent',
            '→': 'approaches', '←': 'from', '↔': 'bidirectional',
            '⇒': 'implies', '⇐': 'implied by', '⇔': 'if and only if',
            '∀': 'for all', '∃': 'there exists', '∈': 'in',
            '∉': 'not in', '⊂': 'subset', '⊃': 'superset',
            '∪': 'union', '∩': 'intersection', '∅': 'empty set',
            '∧': 'and', '∨': 'or', '¬': 'not',
        }

        self.greek_replacements = {
            'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta',
            'ε': 'epsilon', 'ζ': 'zeta', 'η': 'eta', 'θ': 'theta',
            'ι': 'iota', 'κ': 'kappa', 'λ': 'lambda', 'μ': 'mu',
            'ν': 'nu', 'ξ': 'xi', 'π': 'pi', 'ρ': 'rho',
            'σ': 'sigma', 'τ': 'tau', 'υ': 'upsilon', 'φ': 'phi',
            'χ': 'chi', 'ψ': 'psi', 'ω': 'omega',
            'Α': 'Alpha', 'Β': 'Beta', 'Γ': 'Gamma', 'Δ': 'Delta',
            'Ε': 'Epsilon', 'Ζ': 'Zeta', 'Η': 'Eta', 'Θ': 'Theta',
            'Ι': 'Iota', 'Κ': 'Kappa', 'Λ': 'Lambda', 'Μ': 'Mu',
            'Ν': 'Nu', 'Ξ': 'Xi', 'Π': 'Pi', 'Ρ': 'Rho',
            'Σ': 'Sigma', 'Τ': 'Tau', 'Υ': 'Upsilon', 'Φ': 'Phi',
            'Χ': 'Chi', 'Ψ': 'Psi', 'Ω': 'Omega',
        }

    def preprocess(self, text: Optional[str]) -> str:
        """Thoroughly cleans and normalizes document text."""
        if not text:
            return ""

        # Step 0: HTML entity unescaping
        text = html.unescape(text)

        # Step 1: Normalize newlines
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Step 2: Strip Markdown code blocks or inline code formatting
        text = re.sub(r'```[\s\S]*?```', ' ', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)

        # Step 3: Remove LaTeX commands with braces: \command{text} -> text
        text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)

        # Step 4: Replace known LaTeX symbols
        for latex, rep in self.latex_symbols.items():
            text = text.replace(latex, rep)

        # Step 5: Remove remaining backslash commands: \command -> space
        text = re.sub(r'\\[a-zA-Z]+', ' ', text)

        # Step 6: Remove math delimiters and special braces
        text = re.sub(r'[\$\^_{}\[\]\\]', ' ', text)

        # Step 7: Fix smart quotes and typographic quotes
        text = text.replace('“', '"').replace('”', '"')
        text = text.replace('‘', "'").replace('’', "'")
        text = text.replace('‚', "'").replace('„', '"')
        text = text.replace('‹', '<').replace('›', '>')
        text = text.replace('«', '<<').replace('»', '>>')

        # Step 8: Fix dashes and hyphens
        text = text.replace('—', ' - ').replace('–', ' - ')
        text = text.replace('−', '-')

        # Step 9: Fix ellipsis and bullet points
        text = text.replace('…', '...')
        text = text.replace('•', ' ').replace('·', ' ')
        text = text.replace('†', ' ').replace('‡', ' ')
        text = text.replace('§', ' ').replace('¶', ' ')

        # Step 10: Unicode Math and Greek replacements
        for unicode_char, replacement in self.math_replacements.items():
            text = text.replace(unicode_char, replacement)
        for greek, replacement in self.greek_replacements.items():
            text = text.replace(greek, replacement)

        # Step 11: Remove odd non-printable control characters (retain \n, \t, etc)
        text = "".join(ch for ch in text if ch.isprintable() or ch in '\n\t')

        # Step 12: Clean excessive symbols but retain standard English punctuation
        text = re.sub(r'[^\w\s.,;:!?\-\'"]', ' ', text)

        # Step 13: Spacing normalization
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()


preprocessor = TextPreprocessor()

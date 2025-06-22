from transformers import MBartForConditionalGeneration, MBart50Tokenizer
import re

class Translator:
    """
    Handles multilingual translation using mBART-50.
    Also preserves technical terms by replacing them with placeholders.
    """
    def __init__(self, model_name:str = "facebook/mbart-large-50-many-to-many-mmt"):
        print(f"Loading mBART translation model...")
        self.model = MBartForConditionalGeneration.from_pretrained(model_name)
        self.tokenizer = MBart50TokenizerFast.from_pretrained(model_name)
        print("mBART model loaded.")

        self.lang_code_map = {
           "en": "en_XX", "es": "es_XX", "fr": "fr_XX", "de": "de_DE", "ja": "ja_XX",
            "hi": "hi_IN", "zh": "zh_CN", "ar": "ar_AR", "pt": "pt_PT", "ru": "ru_RU" 
        }

    def _extract_technical_terms(self, text:str) -> (str, dict):
        """
        Identifies technical terms and replaces them with placeholders. 
        Helps prevent mistranslation of domain-specific words.
        """    
        term_pattern = r'\b([A-Z][a-zA-Z0-9_]+[A-Z]|[A-Z]{2,}|[A-Za-z]+[0-9]+[A-Za-z_]*)\b'
        terms = re.findall(term_pattern, text)

        placeholder_mapp = {}
        for i, term in enumerate(set(terms)):
            placeholder = f"__TERM{i}__"
            text = re.sub(r'\b' + re.escape(term) + r'\b', placeholder, text)
            placeholder_map[placeholder] = term

        return text, placeholder_map
    
    def _reinsert_technical_terms(self, translated_text: str, placeholder_map: dict) -> str:
        """
        Replaces placeholders with original technical terms.
        """
        for placeholder, term in placeholder_map.items():
            translated_text = re.sub(r'\s*' + re.escape(placeholder) + r'\s*', f' {term} ', translated_text)

        return translated_text.strip()

    def translate_segments(self, segments: list, src_lang: str, target_lang: str, preserve_technical: bool) -> list:
        """
        Translates each transcription segment to the desired target language.
        Preserves technical terms if requested.
        """
        print(f"Step 3: Translating {len(segments)} segments from {src_lang} to {target_lang}...")
        translated_segments = []

        for segment in segments:
            original_text = segment['text']
            placeholder_map = {}
            text_to_translate = original_text

            if preserve_technical:
                text_to_translate, placeholder_map = self._extract_technical_terms(original_text)

            try:
                self.tokenizer.src_lang = self.lang_code_map.get(src_lang, "en_XX")
                encoded_text = self.tokenizer(text_to_translate, return_tensors="pt")
                target_lang_id = self.tokenizer.lang_code_to_id[self.lang_code_map.get(target_lang, "es_XX")]
                generated_tokens = self.model.generate(**encoded_text, forced_bos_token_id=target_lang_id)
                translated_text = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]

                if preserve_technical:
                    translated_text = self._reinsert_technical_terms(translated_text, placeholder_map)

                new_segment = segment.copy()
                new_segment['text'] = translated_text
                translated_segments.append(new_segment)

            except Exception as e:
                print(f"Error translating '{original_text}': {e}")
                translated_segments.append(segment)

        print(f"Translation to {target_lang} complete.")
        return translated_segments
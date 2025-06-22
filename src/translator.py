# src/translator.py
from transformers import MBartForConditionalGeneration, MBart50TokenizerFast
import re

class Translator:
    def __init__(self, model_name: str = "facebook/mbart-large-50-many-to-many-mmt"):
        print("Loading mBART translation model...")
        self.model = MBartForConditionalGeneration.from_pretrained(model_name)
        self.tokenizer = MBart50TokenizerFast.from_pretrained(model_name)
        print("mBART model loaded.")
        # Added 'vi_VN' for Vietnamese
        self.lang_code_map = {
           "en": "en_XX", "es": "es_XX", "fr": "fr_XX", "de": "de_DE", "ja": "ja_XX",
           "zh": "zh_CN", "hi": "hi_IN", "pt": "pt_PT", "ko": "ko_KR", "ta": "ta_IN",
           "uk": "uk_UA", "ru": "ru_RU", "ar": "ar_AR", "vi": "vi_VN"
        }

    def _extract_technical_terms(self, text: str) -> (str, dict):
        term_pattern = r'\b([A-Z][a-zA-Z0-9_]+[A-Z]|[A-Z]{2,}|[A-Za-z]+[0-9]+[A-Za-z_]*)\b'
        terms = re.findall(term_pattern, text)
        
        placeholder_map = {}
        for i, term in enumerate(set(terms)):
            placeholder = f"__TERM{i}__"
            text = re.sub(r'\b' + re.escape(term) + r'\b', placeholder, text)
            placeholder_map[placeholder] = term
        
        return text, placeholder_map
    
    def _reinsert_technical_terms(self, translated_text: str, placeholder_map: dict) -> str:
        for placeholder, term in placeholder_map.items():
            translated_text = re.sub(r'\s*' + re.escape(placeholder) + r'\s*', f' {term} ', translated_text)
        return translated_text.strip()

    def translate_segments(self, segments: list, src_lang: str, target_lang: str, preserve_technical: bool) -> list:
        print(f"Step 3: Translating {len(segments)} segments from {src_lang} to {target_lang}...")
        
        # Ensure source and target languages are supported
        src_lang_code = self.lang_code_map.get(src_lang)
        target_lang_code = self.lang_code_map.get(target_lang)

        if not src_lang_code or not target_lang_code:
            raise ValueError("Unsupported source or target language for translation.")

        translated_segments = []
        original_texts = [segment['text'] for segment in segments]
        
        # Batch processing placeholder logic
        processed_texts = []
        placeholder_maps = []
        if preserve_technical:
            for text in original_texts:
                processed_text, placeholder_map = self._extract_technical_terms(text)
                processed_texts.append(processed_text)
                placeholder_maps.append(placeholder_map)
        else:
            processed_texts = original_texts

        try:
            self.tokenizer.src_lang = src_lang_code
            encoded_batch = self.tokenizer(processed_texts, return_tensors="pt", padding=True, truncation=True)
            
            target_lang_id = self.tokenizer.lang_code_to_id[target_lang_code]
            generated_tokens = self.model.generate(**encoded_batch, forced_bos_token_id=target_lang_id)
            
            translated_batch = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)

            for i, translated_text in enumerate(translated_batch):
                final_text = translated_text
                if preserve_technical:
                    final_text = self._reinsert_technical_terms(translated_text, placeholder_maps[i])
                
                new_segment = segments[i].copy()
                new_segment['text'] = final_text
                translated_segments.append(new_segment)

        except Exception as e:
            print(f"Error during batch translation: {e}. Falling back to individual translation.")
            # Fallback to segment-by-segment if batch fails (less efficient but more robust)
            return super().translate_segments(segments, src_lang, target_lang, preserve_technical)

        print(f"Translation to {target_lang} complete.")
        return translated_segments

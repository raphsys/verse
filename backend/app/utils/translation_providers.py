import requests

class BaseTranslator:
    def translate(self, text: str, source_lang: str, target_lang: str) -> dict:
        raise NotImplementedError

class LibreTranslateProvider(BaseTranslator):
    # Public instance de démonstration, usage limité : https://libretranslate.com/docs/
    ENDPOINT = "http://localhost:5000/translate"

    def translate(self, text: str, source_lang: str = None, target_lang: str = "en") -> dict:
        payload = {
            "q": text,
            "source": source_lang or "auto",
            "target": target_lang,
            "format": "text",
        }
        r = requests.post(self.ENDPOINT, json=payload, timeout=15)
        r.raise_for_status()
        data = r.json()
        return {
            "translated_text": data["translatedText"],
            "detected_source_lang": data.get("detectedSourceLanguage", source_lang or "unknown"),
            "provider": "LibreTranslate"
        }

# Tu peux ajouter ici OpenAIProvider, DeepLProvider, etc.
# class OpenAIProvider(BaseTranslator):
#     def translate(...): ...

# Pour basculer de provider :
TRANSLATORS = {
    "libre": LibreTranslateProvider(),
    # "openai": OpenAIProvider(),
    # "deepl": DeepLProvider(),
}

def get_translator(provider_name="libre"):
    return TRANSLATORS.get(provider_name, LibreTranslateProvider())


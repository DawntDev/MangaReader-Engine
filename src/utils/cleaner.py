import re

class Cleaner:
    
    @staticmethod
    def text(text: str) -> str:
        # Remove URLs
        text_without_urls = re.sub(r"http\S+", "", text)
        cleaned_text = "".join(
            char for char in text_without_urls 
            if char.isalnum() or char == " "
        )
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
        return cleaned_text
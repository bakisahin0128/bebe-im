# config.py

# config.py

# Local API'ler
GENERATE_DESCRIPTION_API_URL = "http://127.0.0.1:8000/generate_job_description"
FIND_CV_API_URL = "http://127.0.0.1:8001/find-best-cv"


# Logger ayarı (örnek)
import logging
app_logger = logging.getLogger("app_logger")
app_logger.setLevel(logging.INFO)

# Konsola yazdırıcı ekliyoruz
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Log formatı
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Logger'a handler ekle
app_logger.addHandler(console_handler)

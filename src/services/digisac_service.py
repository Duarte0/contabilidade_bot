import requests
from core.config import API_BASE_URL, DIGISAC_TOKEN


class DigisacAPI:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {DIGISAC_TOKEN
}",
            "Content-Type": "application/json"
        }

    def enviar_mensagem(self, contact_id, mensagem):
        payload = {
            "contactId": contact_id,
            "text": mensagem
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def listar_contatos(self):
        try:
            all_contatos = []
            page = 1
            
            while True:
                response = requests.get(
                    f"{self.base_url}/contacts",
                    headers=self.headers,
                    params={"perPage": 200, "page": page},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    contatos = data.get('data', [])
                    
                    if not contatos:
                        break
                        
                    all_contatos.extend(contatos)
                    
                    if page >= data.get('lastPage', 1):
                        break
                        
                    page += 1
                else:
                    break
                    
            return all_contatos
        except requests.exceptions.RequestException:
            return []

    def _make_request(self, method, endpoint, payload=None):
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            elif method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, params=payload, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, json=payload, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=30)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro {method} para {url}: {str(e)}")
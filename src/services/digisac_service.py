import requests
from typing import Optional, Dict, Any, List
from core.config import API_BASE_URL, DIGISAC_TOKEN

class DigisacAPI:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {DIGISAC_TOKEN}",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def enviar_mensagem(self, contact_id: str, mensagem: str) -> bool:
        """Envia mensagem para contato com retry simples"""
        payload = {"contactId": contact_id, "text": mensagem}
        
        try:
            response = self.session.post(
                f"{self.base_url}/messages",
                json=payload,
                timeout=10
            )
            return response.status_code == 200
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            return False

    def listar_contatos(self) -> List[Dict[str, Any]]:
        """Lista todos os contatos com paginação otimizada"""
        all_contatos = []
        page = 1
        
        try:
            while True:
                response = self.session.get(
                    f"{self.base_url}/contacts",
                    params={"perPage": 200, "page": page},
                    timeout=15
                )
                
                if response.status_code != 200:
                    break
                    
                data = response.json()
                contatos = data.get('data', [])
                
                if not contatos:
                    break
                    
                all_contatos.extend(contatos)
                
                if page >= data.get('lastPage', 1):
                    break
                    
                page += 1
                
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            pass
            
        return all_contatos

    def _make_request(self, method: str, endpoint: str, payload: Optional[Dict] = None) -> requests.Response:
        """Método genérico para requests com tratamento de erro"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            method = method.upper()
            request_method = getattr(self.session, method.lower())
            
            kwargs = {'timeout': 15}
            if method in ['POST', 'PUT']:
                kwargs['json'] = payload
            else:
                kwargs['params'] = payload
            
            response = request_method(url, **kwargs)
            response.raise_for_status()
            return response
            
        except requests.exceptions.Timeout:
            raise Exception(f"Timeout na requisição {method} para {url}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro {method} para {url}: {str(e)}")

    def get_contact_info(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Busca informações específicas de um contato"""
        try:
            response = self._make_request('GET', f'/contacts/{contact_id}')
            return response.json()
        except Exception:
            return None

    def close(self):
        """Fecha a sessão HTTP"""
        self.session.close()
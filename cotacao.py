import requests
import time
import hmac
import hashlib
import json
import datetime
import pytz
import smtplib
import email.message

def consulta_location():
    informacoes = []
    cotacao = []
    latlong = []

    url = 'https://buscacepinter.correios.com.br/app/cep/carrega-cep.php'
        
    for cep in range(6750001, 6799999):
        try:
            #RETIRA A QUEBRA DE LINHA DO CEP E FAZ A CONSULTA NO VIACEP
            cep = '0' + str(cep)

            payload = {
                'mensagem_alerta': '', 
                'cep': str(cep),
                'cepaux': ''
            }

            response = requests.post(url=url, data=payload)
            objects = json.loads(response.content)
            obj = objects['dados'][0]
            if obj.get('uf') != '':
                
                if obj.get('nomeUnidade') != '':
                    logradouro = str(obj.get('nomeUnidade') + ", " + obj.get('logradouroDNEC') + ", " + obj.get('bairro') + ", " + obj.get('localidade') + ", " + obj.get('uf') + ", " + obj.get('cep'))
                else:
                    logradouro = str(obj.get('logradouroDNEC') + ", " + obj.get('bairro') + ", " + obj.get('localidade') + ", " + obj.get('uf') + ", " + obj.get('cep'))
            
                #FAZ A CONSULTA NO GOOGLE PASSANDO O LOGRADOURO ANTERIOR
                #FAZ A CONVERSAO EM JSON DO RETORNO, E VAI CAMINHANDO
                #NO MESMO ATE CONSEGUIR ACESSAR AS VAVIAVEIS DE LAT E LON
                response2 = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address='+logradouro+'&key=AIzaSyDg6r8iO3Cd_9bt3g0Wjda3yz88MnPrY3k')
                google = json.loads(response2.content)
                
                google = google['results']
                google = google[0]

                lat = str(google['geometry'].get('location').get('lat'))
                lon = str(google['geometry'].get('location').get('lng'))
                
                #CHAMADA DA FUNCAO DE COTACAO DA LALAMOVE
                valor = quotations(lat, lon, logradouro)
                cotacao.append(str(cep + " - " + valor))
                latlong.append(str(lat+","+lon))
                print(cep, valor)
                

        except:
            print(cep, ', Falhou')
    
    #CHAMA A FUNCAO DE GRAVAR NO ARQUIVO
    gravar(cotacao, "cotacao.txt")
    gravar(latlong, "latlong.txt")
    enviar_email()


#FUNCAO PARA GRAVAR OS DADOS NO ARQUIVO TEXTO ESCOLHIDO
def gravar(array, arquivo):
    arq = open(arquivo, "r")
    conteudo = arq.readlines()

    for lnh in array:
        conteudo.append(lnh)
        conteudo.append('\n')
    
    arq = open(arquivo, "w")
    arq.writelines(conteudo)
    arq.close()

    print('SUCESSO NA GRAVACAO: ' + arquivo)

#FUNCAO PARA COTACAO NA LALAMOVE
def quotations(lat, lon, endereco):
    #CHAVES PRODUCAO
    key = 'pk_prod_8582241d46f8c48345011dd5e371b9df'
    secret = 'sk_prod_rRCfqxMZYq/vxldmNlCdsbWhxoFMb7hARSFKHxAtnhv2DVnRc08KpUNje5p6+xNf'

    path = '/v2/quotations'
    region = 'BR_SAO'
    method = 'POST'
    timestamp = int(round(datetime.datetime.timestamp(datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))) * 1000))
    
    body = {
        "serviceType": "LALAPRO",
        "specialRequests": [],
        "requesterContact": {
            "name": 'Gabriela Silva',
            "phone": '11947834435'
        },
        "stops": [
            {
                "location": {
                    "lat": "-23.547561",
                    "lng": "-46.6192263"
                },
                "addresses": {
                    "pt_BR": {
                        "displayString": "Rua Piratininga, 283/285, Brás, São Paulo, SP, 03042-001",
                        "market": region
                    }
                }
            },
            {
                "location": {
                    "lat": lat,
                    "lng": lon
                },
                "addresses": {
                    "pt_BR": {
                        "displayString": endereco,
                        "market": region
                    }
                }
            }
        ],
        "deliveries": [
            {
                "toStop": 1,
                "toContact": {
                    "name": 'Gabriela Silva ou Eduardo',
                    "phone": '11947834435'
                },
                "remarks": "RETIRAR PEDIDO"
            }
        ]
    }
    rawSignature = "{timestamp}\r\n{method}\r\n{path}\r\n\r\n{body}".format(
        timestamp=timestamp, method=method, path=path, body=json.dumps(body))
    signature = hmac.new(secret.encode(), rawSignature.encode(),
                        hashlib.sha256).hexdigest()
    
    url = "https://rest.lalamove.com"

    headers = {
        'Content-type': 'application/json; charset=utf-8',
        'Authorization': "hmac {key}:{timestamp}:{signature}".format(key=key, timestamp=timestamp, signature=signature),
        'Accept': 'application/json',
        'X-LLM-Market': region
    }
    
    r = requests.post(url+path, data=json.dumps(body), headers=headers)
    #print(r.text)
    teste = json.loads(r.content)

    return teste['totalFee']

def enviar_email(): 
    corpo_email = '<p>A cotação acabou.</p>'

    msg = email.message.Message()
    msg['Subject'] = 'Cotação'
    msg['From'] = 'minhavezsistema@gmail.com'
    msg['To'] = 'viniciuscarneiro007@gmail.com'
    password = 'carneiro007'
    msg.add_header('Content-Type', 'text/html')
    msg.set_payload(corpo_email )

    s = smtplib.SMTP('smtp.gmail.com: 587')
    s.starttls()
    # Login Credentials for sending the mail
    s.login(msg['From'], password)
    s.sendmail(msg['From'], [msg['To']], msg.as_string().encode('utf-8'))
    print('Email enviado')

consulta_location()


import json
import logging

import requests
from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response

_LLM_SERVER = 'http://localhost:8000'

logger = logging.getLogger(__name__)


@api_view(http_method_names=['POST'])
def ask_question(request):
    query_str = request.data['query_str']
    resp = requests.post(f'{_LLM_SERVER}/qa/', json={'query_str': query_str})
    llm_resp = json.loads(resp.text)
    for doc in llm_resp['sources']:
        with open('../' + doc['source']) as f:
            if 'nhs_conditions' in doc['source']:
                doc['title'] = ' '.join([w[0].upper() + w[1:].replace('.txt', '')
                                         for w in doc['source'].split('/')[-1].split('-')]).strip()
                doc['link'] = 'https://www.nhs.uk/conditions/' + doc['source'].split('/')[-1].replace('.txt', '')
            elif 'nice_guidelines' in doc['source']:
                line = f.readline()
                if line.strip() == '':
                    line = f.readline()
                doc['title'] = line.strip()
                doc['link'] = 'https://www.nice.org.uk/guidance/' + doc['source'].split('/')[-1].replace('.txt', '')
            else:
                logger.error("Doc source not implemented")
            doc['full_source'] = '\n'.join(f.readlines())
    return Response(llm_resp)


@api_view(http_method_names=['POST'])
def generate_prompt(request):
    query_str = request.data['query_str']
    resp = requests.post(f'{_LLM_SERVER}/gen-prompt/', json={'query_str': query_str})
    return Response(json.loads(resp.text))


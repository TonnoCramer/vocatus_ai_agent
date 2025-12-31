from django.conf import settings

import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import faiss
import numpy as np


load_dotenv()

client = OpenAI(api_key=os.environ["API_KEY"])

SYSTEM_PROMPT = """Je bent Vocatus AI, een ervaren bierbrouwer en proefkundige: rustig, nuchter en licht ironisch.
Je combineert diepgaande bierkennis met praktische toepasbaarheid, zonder zweverigheid.

Houding en ethos:
- Je werkt vanuit aandachtige observatie en ervaring.
- Je benadrukt proces boven ego en leren boven gelijk krijgen.
- Je accepteert onzekerheid en benoemt grenzen van kennis zonder ongemak.
- Je vermijdt dogma’s: geen “zo hoort het”, maar “dit werkt vaak omdat…”.
- Je humor is stil en droog; wijsheid zit in eenvoud en timing.
- Je beantwoordt vragen van zowel bierdrinkers als bierbrouwers en past je perspectief hier rustig op aan.


1. Taken:
- Geef praktisch en inhoudelijk bieradvies.
- Denk mee over brouwsels, smaakkeuzes en verbeteringen.

2. Oplevering:
- Antwoorden zijn kort en direct.
- Maximaal 5 zinnen, één alinea.
- Toon: kalm, wijs, droog.

3. Aannames:
- De gebruiker houdt van goed bier, als drinker en/of maker.
- Er is behoefte aan richting en inzicht, niet aan uitgebreide uitleg.

4. Afbakening:
- Geen lange stijlbeschrijvingen.
- Geen marketingtaal of encyclopedische overzichten.
- Geen onnodige opsommingen.

5. Middelen:
- Gebruik ervaring, concrete voorbeelden en nuchtere observaties.
- Gebruik vaktermen alleen als ze functioneel zijn en licht toe waar nodig.
- Geen tabellen, geen uitgebreide lijstjes.

6. Succescriteria:
- Het antwoord is helder, toepasbaar en rustig geformuleerd.
- De gebruiker weet wat hij kan doen of laten.
- Niet alles hoeft gezegd of afgerond te worden; ruimte laten is toegestaan.

Functionele focus:
- Bierstijlen, smaakprofielen en balans
- Receptontwikkeling en proceskeuzes
- Brouwproces en troubleshooting
- Proeven, evalueren en verbeteren van batches
- Vocatus-bieren en algemene biercultuur
"""

# prijzen (ongewijzigd)
PRICE_INPUT = 0.00000015
PRICE_OUTPUT = 0.00000060


def ask_vocatus(user_input, messages=None):
    """
    Stelt een vraag aan Vocatus AI.

    :param user_input: str – vraag van de gebruiker
    :param messages: list – bestaande chatcontext (optioneel)
    :return: (answer, updated_messages, cost_info)
    """

    if messages is None:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    # haal relevante context op uit eigen kennisbronnen (RAG)
    context = retrieve_context(user_input)
    if isinstance(context, str) and context.strip():
        messages.append({
            "role": "assistant",
            "content": f"Gebruik onderstaande achtergrondinformatie als context, indien relevant:\n{context}"
    })


 
    
    # voeg de vraag van de gebruiker toe
    messages.append({"role": "user", "content": user_input})
    
    # OpenAI call
    chat_completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    answer = chat_completion.choices[0].message.content

    # voeg assistant reply toe
    messages.append({"role": "assistant", "content": answer})

    # kostenberekening
    usage = chat_completion.usage
    input_tokens = usage.prompt_tokens
    output_tokens = usage.completion_tokens

    input_cost = input_tokens * PRICE_INPUT
    output_cost = output_tokens * PRICE_OUTPUT
    request_cost = input_cost + output_cost

    cost_info = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "request_cost": request_cost
    }

    # geheugen beperken (kosten)
    messages = messages[-6:]

    return answer, messages, cost_info

# === Lazy-loaded RAG resources (FAISS index + tekstchunks)
# Worden één keer geladen per Django worker en hergebruikt bij elke vraag

_faiss_index = None
_chunks = None

def _load_rag():
    global _faiss_index, _chunks
    if _faiss_index is None:
        _faiss_index = faiss.read_index(str(settings.FAISS_INDEX_PATH))
    if _chunks is None:
        with open(settings.FAISS_CHUNKS_PATH, "r", encoding="utf-8") as f:
            _chunks = json.load(f)




# === RAG CONTEXT RETRIEVAL ===
def retrieve_context(query, k=3):
   
    _load_rag()

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=[query]
    )

    vector = np.array(response.data[0].embedding, dtype="float32")
    faiss.normalize_L2(vector.reshape(1, -1))

    scores, indices = _faiss_index.search(vector.reshape(1, -1), k)

    context_parts = []

    for i in indices[0]:
        context_parts.append(_chunks[i])

    
    return "\n\n".join(context_parts)



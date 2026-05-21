import time
import requests
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.config import (
    OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_FALLBACK_MODEL,
    OLLAMA_CLOUD_ENABLED, OLLAMA_CLOUD_URL, OLLAMA_CLOUD_MODEL, OLLAMA_CLOUD_API_KEY
)

HEADER = f"{'Modelo':<25} {'Prompt':<15} {'Output':<15} {'Total (s)':<10} {'TPS':<10} {'Estado'}"
SEP = "-" * len(HEADER)

PROMPTS = [
    ("corto", "Hola, ¿cómo estás?"),
    ("medio", "Explica en 3 líneas qué es el aprendizaje automático y sus aplicaciones principales en la industria actual."),
    ("largo", "Escribe un correo formal de 5 párrafos solicitando una reunión con un cliente importante. Incluye saludo, introducción, agenda propuesta, disponibilidad horaria y despedida cortés."),
]

def test_ollama(url, model, prompts, headers=None, timeout=120):
    results = []
    for label, prompt in prompts:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"num_predict": 256}
        }
        start = time.time()
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=timeout)
            elapsed = time.time() - start
            if r.status_code == 200:
                data = r.json()
                content = (data.get("message", {}) or {}).get("content", "") or ""
                prompt_tokens = (data.get("prompt_eval_count", 0))
                output_tokens = (data.get("eval_count", 0))
                total_tokens = prompt_tokens + output_tokens
                tps = round(output_tokens / elapsed, 1) if elapsed > 0 and output_tokens else 0
                results.append((label, prompt_tokens, output_tokens, round(elapsed, 2), tps, "✅"))
            else:
                results.append((label, 0, 0, round(elapsed, 2), 0, f"⚠️ {r.status_code}"))
        except Exception as e:
            elapsed = time.time() - start
            results.append((label, 0, 0, round(elapsed, 2), 0, f"❌ {e}"))
    return results

def print_results(model_name, results):
    print(f"\n{'='*60}")
    print(f"  {model_name}")
    print(f"{'='*60}")
    print(HEADER)
    print(SEP)
    for label, pt, ot, t, tps, status in results:
        tps_str = f"{tps}" if tps else "-"
        print(f"{model_name:<25} {label:<15} {ot:<15} {t:<10} {tps_str:<10} {status}")
    print()

def main():
    print(f"\n{'#'*60}")
    print(f"  AgentPiro - Speed Test de Modelos")
    print(f"  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    all_results = []

    # 1. Cloud
    if OLLAMA_CLOUD_ENABLED and OLLAMA_CLOUD_API_KEY:
        url = f"{OLLAMA_CLOUD_URL}/api/chat"
        headers = {"Authorization": f"Bearer {OLLAMA_CLOUD_API_KEY}", "Content-Type": "application/json"}
        print(f"\n🌐 Probando Cloud: {OLLAMA_CLOUD_MODEL} ...")
        res = test_ollama(url, OLLAMA_CLOUD_MODEL, PROMPTS, headers)
        print_results(OLLAMA_CLOUD_MODEL, res)
        all_results.append((OLLAMA_CLOUD_MODEL, res))
    else:
        print("\n⏭️  Cloud deshabilitado (sin API key)")

    # 2. Local principal
    url = f"{OLLAMA_HOST}/api/chat"
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if r.status_code == 200:
            print(f"🖥️  Probando Local: {OLLAMA_MODEL} ...")
            res = test_ollama(url, OLLAMA_MODEL, PROMPTS)
            print_results(OLLAMA_MODEL, res)
            all_results.append((OLLAMA_MODEL, res))
        else:
            print("\n⏭️  Local no disponible")
    except Exception as e:
        print(f"\n⏭️  Local no disponible: {e}")

    # 3. Fallback local
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if r.status_code == 200:
            print(f"🖥️  Probando Fallback: {OLLAMA_FALLBACK_MODEL} ...")
            res = test_ollama(url, OLLAMA_FALLBACK_MODEL, PROMPTS)
            print_results(OLLAMA_FALLBACK_MODEL, res)
            all_results.append((OLLAMA_FALLBACK_MODEL, res))
    except:
        pass

    # Resumen
    print(f"\n{'#'*60}")
    print(f"  RESUMEN - TPS (tokens/segundo) por modelo y prompt")
    print(f"{'#'*60}")
    print(f"{'Modelo':<25} {'Corto':<10} {'Medio':<10} {'Largo':<10}")
    print(SEP[:55])
    for model_name, results in all_results:
        tps_vals = [str(r[4]) if r[4] else "-" for r in results]
        print(f"{model_name:<25} {tps_vals[0]:<10} {tps_vals[1]:<10} {tps_vals[2]:<10}")

    print(f"\n✅ Speed test completado.\n")

if __name__ == "__main__":
    main()

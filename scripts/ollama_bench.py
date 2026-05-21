import time
import requests
import sys
import subprocess

OLLAMA_HOST = "http://localhost:11434"
URL = f"{OLLAMA_HOST}/api/chat"

HEADER = f"{'Modelo':<25} {'Prompt':<15} {'Output':<15} {'Total (s)':<10} {'TPS':<10} {'Estado'}"
SEP = "-" * len(HEADER)

PROMPTS = [
    ("logica", "Juan tiene 3 manzanas. Pedro le da 5 manzanas más. Luego Juan pierde la mitad. ¿Cuántas manzanas tiene Juan al final? Explica paso a paso."),
    ("formato", "Escribe exactamente 3 puntos numerados (1., 2., 3.) sobre beneficios de Python. Cada punto debe ser una sola línea. No agregues nada antes ni después."),
    ("creativo", "Inventa una metáfora original que describa cómo funciona una red neuronal. Mínimo 4 líneas, máximo 8. No uses la metáfora del cerebro."),
]

def get_local_models():
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])
                  if not m["name"].startswith("ollama-") and ":" in m["name"]]
        return sorted(models)
    except Exception as e:
        print(f"❌ Error al obtener modelos vía API: {e}")
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
            lines = result.stdout.strip().splitlines()[1:]
            models = []
            for line in lines:
                parts = line.split()
                if parts:
                    models.append(parts[0])
            return models
        except Exception as e2:
            print(f"❌ Error al ejecutar ollama list: {e2}")
            sys.exit(1)

def test_model(model, prompts, timeout=300):
    results = []
    outputs = []
    for label, prompt in prompts:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"num_predict": 512}
        }
        start = time.time()
        try:
            r = requests.post(URL, json=payload, timeout=timeout)
            elapsed = time.time() - start
            if r.status_code == 200:
                data = r.json()
                prompt_tokens = data.get("prompt_eval_count", 0)
                output_tokens = data.get("eval_count", 0)
                content = data.get("message", {}).get("content", "")
                tps = round(output_tokens / elapsed, 1) if elapsed > 0 and output_tokens else 0
                results.append((label, prompt_tokens, output_tokens, round(elapsed, 2), tps, "✅"))
                outputs.append((label, content))
            else:
                results.append((label, 0, 0, round(elapsed, 2), 0, f"⚠️ {r.status_code}"))
                outputs.append((label, ""))
        except Exception as e:
            elapsed = time.time() - start
            results.append((label, 0, 0, round(elapsed, 2), 0, f"❌ {e}"))
            outputs.append((label, ""))
    return results, outputs

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

def print_outputs(model_name, outputs):
    print(f"{'─'*60}")
    print(f"  OUTPUTS - {model_name}")
    print(f"{'─'*60}")
    for label, content in outputs:
        print(f"\n  ▶ [{label}]")
        print(f"  {content}")
    print()

def main():
    print(f"\n{'#'*60}")
    print(f"  Ollama Local Benchmark")
    print(f"  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    models = get_local_models()
    if not models:
        print("❌ No se encontraron modelos locales.")
        sys.exit(1)

    print(f"\nModelos encontrados: {', '.join(models)}\n")

    all_results = []
    for model in models:
        print(f"🖥️  Probando {model} ...")
        res, outs = test_model(model, PROMPTS)
        print_results(model, res)
        print_outputs(model, outs)
        all_results.append((model, res))

    print(f"\n{'#'*60}")
    print(f"  RESUMEN - TPS (tokens/segundo) por modelo y prompt")
    print(f"{'#'*60}")
    print(f"{'Modelo':<25} {'Corto':<10} {'Medio':<10} {'Largo':<10}")
    print(SEP[:55])
    for model_name, results in all_results:
        tps_vals = [str(r[4]) if r[4] else "-" for r in results]
        print(f"{model_name:<25} {tps_vals[0]:<10} {tps_vals[1]:<10} {tps_vals[2]:<10}")

    print(f"\n✅ Benchmark completado.\n")

if __name__ == "__main__":
    main()

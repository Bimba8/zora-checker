import requests
import time
import json
from decimal import Decimal, ROUND_DOWN

# Функция для отправки GraphQL-запроса
def get_zora_tokens(wallet_address, retries=50, delay=1):
    url = "https://api.zora.co/universal/graphql"
    query = """
    query graph {
      zoraTokenAllocation(identifierWalletAddresses: "ADDRESS") {
        totalTokensEarned {
          totalTokens
        }
      }
    }
    """
    # Заменяем ADDRESS на текущий адрес кошелька
    query = query.replace("ADDRESS", wallet_address)
    payload = {"query": query}

    for attempt in range(retries):
        try:
            response = requests.post(url, json=payload)
            data = response.json()

            # Проверяем на ошибки лимита
            if "errors" in data and any("Rate limit exceeded" in error["message"] for error in data["errors"]):
                print(f"Rate limit exceeded for {wallet_address}, retrying in {delay} seconds...")
                time.sleep(delay)
                continue
            elif "detail" in data and "Ratelimit exceeded" in data["detail"]:
                print(f"Rate limit exceeded for {wallet_address}, retrying in {delay} seconds...")
                time.sleep(delay)
                continue

            # Проверяем успешный ответ
            if "data" in data and data["data"] and data["data"].get("zoraTokenAllocation"):
                total_tokens = data["data"]["zoraTokenAllocation"]["totalTokensEarned"]["totalTokens"]
                # Округляем до двух знаков после запятой
                rounded_tokens = Decimal(str(total_tokens)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
                return float(rounded_tokens)
            else:
                print(f"Не удалось получить данные для {wallet_address}: {data}")
                return None

        except Exception as e:
            print(f"Ошибка при запросе для {wallet_address}: {e}")
            time.sleep(delay)
            continue

    print(f"Не удалось получить данные для {wallet_address} после {retries} попыток.")
    return None

# Чтение адресов из файла и обработка
def process_wallets():
    input_file = "wallets.txt"
    output_file = "results.txt"
    
    try:
        with open(input_file, "r") as f:
            wallets = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Файл wallets.txt не найден. Создайте его и добавьте адреса кошельков (по одному в строке).")
        return

    results = []
    total_tokens_sum = Decimal('0.00')  # Для хранения суммы токенов

    for wallet in wallets:
        print(f"Проверяю адрес: {wallet}")
        tokens = get_zora_tokens(wallet)
        if tokens is not None:
            result = f"{wallet}: {tokens}"
            print(result)
            results.append(result)
            # Добавляем токены к общей сумме
            total_tokens_sum += Decimal(str(tokens))
        else:
            result = f"{wallet}: Ошибка получения данных"
            print(result)
            results.append(result)

    # Округляем сумму до двух знаков после запятой
    total_tokens_sum = total_tokens_sum.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
    total_result = f"\nОбщая сумма токенов: {total_tokens_sum}"
    print(total_result)
    results.append(total_result)

    # Сохраняем результаты в файл
    with open(output_file, "w") as f:
        for result in results:
            f.write(result + "\n")
    print(f"Результаты сохранены в {output_file}")

# Запуск скрипта
if __name__ == "__main__":
    process_wallets()
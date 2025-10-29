# 🧪 PKI Site Health Check

Набор bash-скриптов для проверки доступности и корректности публичных PKI‑сервисов ZETES / eID PKI (Эстония).

## 📂 Структура
- `pki_check.sh`: проверка PDF, CRT и CRL репозиториев
- `check_ocsp.sh`: проверка OCSP‑эндпойнта и статуса сертификатов
- `check_ldap.sh`: проверка доступности LDAP/LDAPS и выборки
- `pki_monitor.sh`: единый скрипт‑оркестратор с итоговой сводкой
- `artifacts/`: папка для загруженных артефактов (PDF, CRT, CRL)
- `results.csv`: общий CSV‑отчёт со всеми результатами

## ⚙️ Требования
- `bash`, `curl`, `openssl`, `ldap-utils`, `coreutils`
- доступ в интернет к сервисам `*.eidpki.ee`

## 🚀 Запуск
```bash
chmod +x *.sh
./pki_monitor.sh
```

### 🔑 Важно для OCSP‑проверки
Для корректной работы OCSP‑проверки необходимо, чтобы следующие файлы находились в директории:

```text
./artifacts/crt/EEGovCA2025.crt
./artifacts/crt/ESTEID2025.crt
```

Они используются как issuer и cert при выполнении запроса к `https://ocsp.eidpki.ee`.

### 🧾 Пример вывода
```text
📄 PDF:  9/9 OK
🔏 CRT:  2/2 OK
🚫 CRL:  2/2 OK
🧩 OCSP: 1/1 OK
📡 LDAP: 2 searches OK, 2 ports OK
✅ Проверка завершена
```

Все результаты логируются в `results.csv` и сохраняются для последующего анализа.

# Pokemon Game Database Manager

Bu uygulama, Pokemon oyunu için gerekli verileri (Pokemon, Move, Item) yönetmek ve düzenlemek için tasarlanmış bir veritabanı yönetim sistemidir.

## Özellikler

- Pokemon, Move ve Item verilerini düzenleme
- Verileri JSON formatında kaydetme
- Kullanıcı dostu arayüz
- Unity ile uyumlu veri formatı

## Kurulum

1. Python 3.8 veya daha yüksek bir sürümü yükleyin
2. Gerekli paketleri yükleyin:
   ```
   pip install -r requirements.txt
   ```
3. Uygulamayı başlatın:
   ```
   python main.py
   ```

## Kullanım

1. Uygulama başlatıldığında ana menüden Pokemon, Move veya Item verilerini seçebilirsiniz
2. Verileri düzenleyebilir, yeni veri ekleyebilir veya mevcut verileri silebilirsiniz
3. Değişiklikleri JSON formatında kaydedebilirsiniz
4. Kaydedilen JSON dosyasını Unity projenizde kullanabilirsiniz

## Veri Yapısı

### Pokemon
```json
{
    "id": "int",
    "name": "string",
    "type": ["string"],
    "base_stats": {
        "hp": "int",
        "attack": "int",
        "defense": "int",
        "sp_attack": "int",
        "sp_defense": "int",
        "speed": "int"
    },
    "moves": ["string"],
    "evolution": {
        "next_form": "string",
        "level": "int"
    }
}
```

### Move
```json
{
    "id": "int",
    "name": "string",
    "type": "string",
    "power": "int",
    "accuracy": "int",
    "pp": "int",
    "category": "string",
    "description": "string"
}
```

### Item
```json
{
    "id": "int",
    "name": "string",
    "type": "string",
    "description": "string",
    "effect": "string",
    "price": "int"
}
``` 
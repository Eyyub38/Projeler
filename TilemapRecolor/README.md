# Tileset Recolor

Bu program, pixel art tileset'lerinizi farklı renk paletleriyle yeniden renklendirmenizi sağlar.

## Gereksinimler

- Python 3.7 veya üzeri
- Pillow (PIL)
- NumPy

## Kurulum

1. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

## Kullanım

1. Programı çalıştırın:
```bash
python tileset_recolor.py
```

2. Program sizden aşağıdaki bilgileri isteyecektir:
   - Tileset resminizin yolu
   - Orijinal renk paleti resminizin yolu
   - Yeni renk paleti resminizin yolu
   - Çıktı dosyasının kaydedileceği yol

## Renk Paleti Formatı

Renk paleti resimleri şu şekilde olmalıdır:
- Her renk, resimde bir piksel olarak temsil edilir
- Renkler yan yana dizilmelidir
- Siyah pikseller (0,0,0) göz ardı edilir
- Orijinal ve yeni paletlerde aynı sayıda renk olmalıdır

## Örnek

1. Orijinal tileset'inizi hazırlayın
2. Orijinal tileset'in renk paletini bir resim olarak hazırlayın
3. Yeni renk paletini bir resim olarak hazırlayın
4. Programı çalıştırın ve istenen dosya yollarını girin
5. Yeniden renklendirilmiş tileset'iniz belirttiğiniz konuma kaydedilecektir 
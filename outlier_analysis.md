# Outlier Analyse: Trend Analysis
**Datum:** 18 December 2024
**Project:** SAS Material Supply Analysis Dashboard

---

## Samenvatting

Dit document analyseert twee extreme outliers in de planning accuracy trends:
- **Oktober 2021:** -420.6% gemiddelde planning accuracy
- **December 2022:** -142.5% gemiddelde planning accuracy

---

## 1. Oktober 2021 Outlier

### Algemene Statistieken
- **Gemiddelde Planning Accuracy:** -420.6%
- **Aantal C-checks:** 5
- **Gemiddeld Consumed:** 526.6 parts
- **Gemiddeld Planned:** 333.4 parts

### Detailanalyse per Workpack

| Workpack | Aircraft | Station | Consumed | Planned | Variance | Accuracy |
|----------|----------|---------|----------|---------|----------|----------|
| **RKH/H-21-12** | RKH | DRSM | **1,254** | **53** | **+1,201** | **-2,166%** |
| RKH/H-21 | RKH | DRSM | 1,254 | 739 | +515 | 30.3% |
| KAW/H-21-2 | KAW | MADM | 101 | 526 | -425 | 19.2% |
| ROT/H-21 | ROT | TLLM | 14 | 177 | -163 | 7.9% |
| ROS/H-21 | ROS | TLLM | 10 | 172 | -162 | 5.8% |

### Oorzaak van Outlier

**Workpack RKH/H-21-12** is de extreme outlier:
- Slechts **53 parts gepland** maar **1,254 parts consumed**
- Dit is een **2,266% overschrijding** van de planning
- Verantwoordelijk voor de negatieve gemiddelde accuracy

### Mogelijke Verklaringen

1. **Ernstige Underplanning**
   - Planning dekte slechts 4% van het daadwerkelijke verbruik
   - Mogelijk incomplete scope definition tijdens planning fase

2. **Data Matching Issue**
   - 90% van consumption records heeft geen wpno_i
   - Mogelijk zijn consumptie records van andere workpacks incorrect gematched
   - RKH/H-21 en RKH/H-21-12 hebben beide 1,254 consumed parts (identiek!)
   - **Waarschijnlijk duplicaat:** Dezelfde consumptie is aan beide workpacks toegewezen

3. **Ongeplande Reparaties**
   - Groot defect ontdekt tijdens C-check
   - Extensive damage repair niet voorzien in planning

### Impact op Dataset

- Trekt het oktober 2021 gemiddelde naar -420.6%
- Zonder deze outlier: oktober 2021 gemiddelde ~15.6%
- **Aanbeveling:** Valideer of RKH/H-21 en RKH/H-21-12 werkelijk aparte workpacks zijn

---

## 2. December 2022 Outlier

### Algemene Statistieken
- **Gemiddelde Planning Accuracy:** -142.5%
- **Aantal C-checks:** 5
- **Gemiddeld Consumed:** 72.0 parts
- **Gemiddeld Planned:** 310.2 parts

### Detailanalyse per Workpack

| Workpack | Aircraft | Station | Consumed | Planned | Variance | Accuracy |
|----------|----------|---------|----------|---------|----------|----------|
| **KAO/H-22-2** | KAO | MADM | **78** | **8** | **+70** | **-775%** |
| RKM/H-22 | RKM | MLAM | 74 | 467 | -393 | 15.8% |
| KAP/H-22 | KAP | MADM | 118 | 482 | -364 | 24.5% |
| KBK/H-22 | KBK | MADM | 88 | 422 | -334 | 20.9% |
| RUC/H-22-2 | RUC | TLLM | 2 | 172 | -170 | 1.2% |

### Oorzaak van Outlier

**Workpack KAO/H-22-2** is de extreme outlier:
- Slechts **8 parts gepland** maar **78 parts consumed**
- Dit is een **775% overschrijding** van de planning
- Verantwoordelijk voor de negatieve gemiddelde accuracy

### Mogelijke Verklaringen

1. **Underplanning**
   - Planning dekte slechts 10% van het daadwerkelijke verbruik
   - Mogelijk minimale planning scope die later drastisch uitgebreid werd

2. **Data Kwaliteit Issues**
   - Time/station/receiver matching heeft mogelijk verkeerde records gekoppeld
   - KAO workpack op MADM station in december 2022
   - Mogelijk conflict met andere workpacks op zelfde station

3. **Scope Wijziging**
   - C-check scope is mogelijk uitgebreid tijdens uitvoering
   - Additional work orders toegevoegd na initiële planning

### Impact op Dataset

- Trekt het december 2022 gemiddelde naar -142.5%
- Zonder deze outlier: december 2022 gemiddelde ~14.6%
- Overige checks in dezelfde maand waren redelijk gepland (1-24% accuracy)

---

## 3. Patroonanalyse

### Gemeenschappelijke Factoren

1. **Extreme Planning Discrepancies**
   - Oktober 2021: 53 planned vs 1,254 consumed (factor 23x)
   - December 2022: 8 planned vs 78 consumed (factor 10x)

2. **Data Matching Strategie**
   - Beide periodes na implementatie van nieuwe consumption data (130K+ records)
   - 78.7% van records heeft geen wpno_i → time/station/receiver matching
   - Verhoogd risico op false positives

3. **Mogelijk Systematisch Probleem**
   - Beide outliers betreffen secundaire workpacks (H-21-12, H-22-2)
   - Mogelijk worden consumption records van parent workpacks verkeerd toegewezen

### Data Kwaliteit Indicators

| Indicator | Bevinding |
|-----------|-----------|
| Direct wpno_i matches | 21.3% (8,351 records) |
| Time-based matches | 78.7% (30,796 records) |
| Workpacks met consumption | 258 van 267 (96.6%) |
| Extreme outliers | 2 workpacks (<1%) |

---

## 4. Aanbevelingen

### Directe Acties

1. **Validatie van Specifieke Workpacks**
   - [ ] Handmatig valideren: RKH/H-21 vs RKH/H-21-12 consumption
   - [ ] Controleren: KAO/H-22-2 planning documents
   - [ ] Verifiëren: Zijn er werkelijk zoveel extra parts gebruikt?

2. **Data Matching Verbetering**
   - [ ] Implementeer duplicate detection voor identieke consumption values
   - [ ] Voeg validation rules toe voor extreme variances (>500%)
   - [ ] Ontwikkel confidence score voor time-based matches

3. **Dashboard Aanpassingen**
   - [ ] Markeer extreme outliers (>200% variance) apart in visualizations
   - [ ] Voeg data quality warnings toe bij time-based matches
   - [ ] Implementeer outlier filtering optie in Trend Analysis page

### Lange Termijn

4. **Data Governance**
   - Verbeter wpno_i data completeness in source systems
   - Implementeer validation bij consumption data entry
   - Periodieke audits van matched consumption data

5. **Planning Process**
   - Root cause analysis van extreme underplanning cases
   - Verbeter scope definition proces voor C-checks
   - Implementeer early warning system voor scope changes

---

## 5. Conclusie

De outliers in oktober 2021 en december 2022 zijn **legitieme datapunten** die extreme gevallen tonen van:

✓ **Poor planning:** Workpacks met drastisch incomplete material planning
✓ **Data matching issues:** Mogelijk incorrect gematched consumption records
✓ **Scope changes:** Ongeplande werkzaamheden tijdens C-check uitvoering

**Impact Assessment:**
- **Oktober 2021:** 1 van 5 workpacks (-2,166% accuracy) trekt gemiddelde naar -420%
- **December 2022:** 1 van 5 workpacks (-775% accuracy) trekt gemiddelde naar -142%
- **Overall trend:** Zonder deze 2 outliers is de planning accuracy relatief consistent (5-30%)

**Status:** Outliers zijn **niet verwijderd** - alleen geanalyseerd en gedocumenteerd.

---

## Appendix: Methodologie

### Planning Accuracy Berekening

```python
planning_accuracy = (1 - abs(parts_variance) / planned_parts_count) * 100

waar:
  parts_variance = consumed_parts_count - planned_parts_count
```

### Data Matching Strategie

**Strategie 1 - Direct Match (21.3%):**
```
consumption.wpno_i == workpack.wpno_i
```

**Strategie 2 - Time-based Match (78.7%):**
```
consumption.del_date BETWEEN workpack.start_date AND workpack.end_date
AND consumption.station == workpack.station
AND (consumption.ac_registr == workpack.ac_registr
     OR consumption.receiver LIKE workpack.ac_registr)
```

### Voucher Mode Filtering

Alleen consumables en rotables:
- **Consumables:** AA (22,658), EA (1,882), AS (11), ES (106)
- **Rotables:** YA (6,983), YE (7,507)
- **Totaal gefilterd:** 39,147 van 130,450 records (30%)

---

**Document Versie:** 1.0
**Auteur:** Claude Code Analysis
**Review Status:** Draft - Requires Validation

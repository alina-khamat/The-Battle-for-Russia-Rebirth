# Model Card — ruBERT Criticism of Russian Authorities Classifier

## Model Overview
**Base model:** [DeepPavlov/rubert-base-cased](https://huggingface.co/DeepPavlov/rubert-base-cased)  
**Architecture:** BERT (12 layers, 768 hidden, 12 heads, ~180M parameters)  
**Task:** Binary sequence classification — *Criticism of Russian authorities (1) vs. Other (0)*  
**Framework:** Hugging Face Transformers (Trainer API)  

---

## Data and Labeling
**Corpus:** Russian Telegram messages sampled from the national-patriotic discourse  
**Training dataset:** 📄 [`criticism_training_data.csv`](../data/Training_Dataset.csv)  

**Label definition:**
- **Criticism (1):** Explicit or implicit negative evaluation of Russian authorities, leadership, or state institutions (including blame, calls for accountability, incompetence/lying frames).  
- **Other (0):** Neutral/positive/non-political content, or political content that assigns blame to *foreign* (non-domestic) authorities.  

**Split:** Stratified 80/20 (train/test)  
**Preprocessing:** Whitespace trim; `max_len = 128`; no oversampling  

---

## ⚙️ Training Configuration

| Parameter | Value |
|------------|--------|
| Optimizer | AdamW |
| Learning rate | 2e-5 |
| Weight decay | 0.01 |
| Batch size | 8 |
| Epochs | 3 |
| Eval / Save | Each epoch |
| Load best at end | ✅ True |
| Tokenizer | DeepPavlov/rubert-base-cased (`max_len=128`, padding/truncation) |
| Inference threshold | 0.5 (tunable via PR curve) |
| Seed | 42 |

---

## Training Dynamics
**Selection criterion:** Lowest validation loss  
**Validation loss by epoch:**  
- E1 = 0.5302  
- **E2 = 0.4649**  
- E3 = 0.4799  

✅ **Best checkpoint:** epoch 2 (used for all reported results)

---

## Held-Out Test Performance

| Class | Precision | Recall | F1 | Support |
|-------|------------|--------|----|----------|
| 0 — Non-criticism | 0.887 | 0.764 | 0.821 | 72 |
| 1 — Criticism | 0.730 | 0.868 | 0.793 | 53 |
| **Accuracy** |   |   | **0.808** | 125 |
| **Macro avg** | 0.809 | 0.816 | 0.807 | 125 |
| **Weighted avg** | 0.821 | 0.808 | 0.809 | 125 |

---

### Confusion Matrix (threshold = 0.5)

|   | **Pred 0** | **Pred 1** |
|---|-------------|------------|
| **True 0** | TN = 55 | FP = 17 |
| **True 1** | FN = 7 | TP = 46 |

---

## FP / FN Examples

| Type | Example (RU) | Example (EN) |
|------|---------------|---------------|
| **FP  p(crit) = 0.83** |*Релокантов-русофобов начали щемить. Им это не нравится. Бежавшие за рубеж музыканты, артисты и стендап-комики, не прекратившие поливать дерьмом родную страну из прекрасного далека, начали возмущаться, что их стали щемить в «цивилизованном мире». Штрафуют, запрещают концерты, сажают в тюрьмы. Общий лейтмотив — ах, какой плохой Кремль! Через МИД выкручивает руки творческой «элите»! А чего вы ждали? Хотели воевать с государством? Ну так будьте готовы к тому, что оно будет защищаться. И давать сдачи. При этом, у государства гораздо больше способов нагадить вам, чем у вас — государству. Если вы плюнете в коллектив, коллектив утрётся. Если коллектив в вас — вы утонете. А сидели бы тихо в своих дубаях и не открывали бы рот на страну, которой обязаны своим благосостоянием, глядишь, и попроще бы жилось.* | *Relocant Russophobes have started to get squeezed. They don’t like it. Musicians, performers, and stand-up comedians who fled abroad and haven’t stopped shitting on their homeland from a comfortable distance have begun complaining that they’re being squeezed in the “civilized world.” They’re being fined, concerts are being banned, they’re being thrown in prison. The general refrain is: “oh, what a bad Kremlin! It’s twisting the arms of the creative ‘elite’ through the Foreign Ministry!” And what did you expect? You wanted to wage war on the state? Then be ready for it to defend itself—and to hit back. Moreover, the state has far more ways to mess with you than you have to mess with the state. If you spit on the collective, the collective will wipe it off. If the collective spits on you—you’ll drown. If only you had kept quiet in your Dubais and not opened your mouths against the country to which you owe your prosperity, you might have had an easier life.* |
| **FP p(crit) = 0.71** |  *Я понимаю, что тыкать всюду с криками "буквально гитлер" — это в современном обществе, так сказать, моветон. Но отметить не могу. Вестоидская пропаганда ОЧЕНЬ похожа на нацистскую. Враг должен быть одновременно жалким и беспомощным, но при этом внушающим страх. Враг в такой пропаганде — враг не из-за своих убеждений, а по модулю, скорее даже не человек, а мрачный доппельгангер европейца. Еврей живёт в антисанитарных условиях, одержим безумными традициями. Он труслив и жаден, слаб. Но ПРИ ЭТОМ евреи проникли во все банки и парламенты, буквально держат наш фатерлянд за яйца, но что САМОЕ СТРАШНОЕ — может ПРИТВОРИТЬСЯ НЕМЦЕМ. То же самое во всех новостях Руины. В Оркостане невозможно жить. Это выжженная пустошь, азиатский деспотат... Но при этом влияние русских распространяется всюду — они повинны и в парижских клопах, и в наводнении в Сенегале. При этом очевидно, что в пропаганде европейских стран Россия предстает некой анти-Европой. Русский может выглядеть как человек, говорить как человек, но в его рептильном мозге кипит жажда насилия, подавленная в европейцах. Русский доппельгангер воплощает желания и страхи европейца. В образе нищего мордора кроются опасения европейцев за своё будущее, а в образе всесильного ФСБ — стремление к власти. Короче, идеальный враг, Абсолютный Другой — одновременно тот, кем ты стать боишься, но при этом он способен выйти за рамки обывательской морали.* | *I understand that running around yelling “literally Hitler” everywhere is, in modern society, so to speak, bad form. But I can’t help noting it. Vestoid propaganda is VERY similar to Nazi propaganda. The enemy has to be both pitiful and helpless, yet at the same time fear-inducing. In such propaganda the enemy is an enemy not because of his convictions, but by definition—rather not even a human, but a gloomy doppelgänger of the European. The Jew lives in unsanitary conditions, obsessed with insane traditions. He is cowardly and greedy, weak. But AT THE SAME TIME the Jews have penetrated all the banks and parliaments, literally have our fatherland by the balls, and—what is MOST TERRIFYING—can PASS AS A GERMAN. The same thing is in all the news from “Ruina.” It’s impossible to live in “Orkostan.” It’s a scorched wasteland, an Asiatic despotate… But at the same time the influence of Russians spreads everywhere—they’re to blame for the bedbugs in Paris and the flooding in Senegal. And it’s obvious that in European countries’ propaganda, Russia appears as a kind of anti-Europe. A Russian can look like a person, speak like a person, but in his reptilian brain there seethes a thirst for violence, suppressed in Europeans. The Russian doppelgänger embodies the desires and fears of the European. In the image of a poor Mordor/dirty shtetl lie Europeans’ anxieties about their own future, and in the image of the Elders of Zion/all-powerful FSB—the striving for power. In short, the ideal enemy, the Absolute Other—at once the one you fear becoming, but at the same time capable of stepping beyond bourgeois morality.* |
| **FN  p(crit) = 0.07** | *Владимир Владимирович, вы так и будете миролюбиво жевать сопли или начнёте отодвигать границу?* | *Vladimir Vladimirovich, are you going to keep meekly dragging your feet or will you start pushing the border back?* |
| **FN p(crit) = 0.11** |  *Прошло 2 года СВО. В декабре 2021 года нам говорили: в армии всё есть! В декабре 2023 года стало понятно, что того, что нужно, нет. Просрали все полимеры, господа генералы. Грубник вам тысячу раз говорил: фронту нужны готовые решения. На что вас хватило — прийти к Коваксу и потребовать у него готовое решение. Так это не работает... Интеллектуально мы — в жопе. Путин сказал — проблема с дронами. ВПК подстроился? Нет. Почему? Никто не может признать 20 лет развития нашей военной науки полным говном. Хотите понять, о чём Путин говорил с генштабом?.. Приезжайте. Прогулка в 1300 метров до Царской охоты — и вы будете молиться, чтоб вернуться в прошлое и заняться рэбом, мастерками, беспилотниками... Вы красили бордюр вместо разработки РЭБ, вели журналы вместо исследований радиосигналов. Живите с этим, твари. Не верьте телевизору — он вещает из Москвы. Приезжайте сами.* | *Two years of the SVO have passed. In December 2021 we were told: the army has everything! In December 2023 it became clear that what is needed is not there. You fucked up all the polymers, gentlemen generals. Grubnik told you a thousand times: the front needs ready-made solutions. What were you capable of—coming to Kovaks and demanding a ready-made solution from him. That’s not how it works… Intellectually we are in deep shit. Putin said—there’s a problem with drones. Did the military-industrial complex adjust? No. Why? No one can bring themselves to admit that 20 years of our military science development is complete shit. Want to understand what Putin talked about with the General Staff?.. Come. A 1,300-meter walk to Tsarskaya Okhota—and you’ll pray to go back in time and take up REB [electronic warfare], trowels, drones… You painted the curb instead of developing EW, kept logbooks instead of researching radio signals and producing components. Live with it, scum. Don’t believe the TV—it broadcasts from Moscow. Come and see for yourselves.* |


---

### Error Analysis Summary
Errors predominantly arise in two contexts. First, false positives occur when a post quotes or paraphrases criticism of Russian authorities (e.g., attributed to Russian liberals or Western elites) and the author rebuts that criticism; the classifier reacts to the intense negative language but fails to recognize that the negativity is not the author’s stance toward domestic authorities. Second, false negatives concentrate in short messages where criticism is expressed primarily through rhetorical questions or direct address to officials, which provide few lexical markers of blame; as a result, the posterior for the “criticism” class is underestimated despite a clear oppositional intent.
 

---

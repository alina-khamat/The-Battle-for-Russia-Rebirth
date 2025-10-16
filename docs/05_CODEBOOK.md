## Codebook

This document describes the structure and  meaning of the datasets and keyword lists used for the “The Battle for Russia Rebirth” project.

## 📄 File: `Nodes.csv`

### Description
Each row represents one Telegram channel (a node) in the directed network.  
Node-level attributes describe the channel’s connectivity, community assignment, and activity.

### Schema

| Column name | Type | Description |
|--------------|------|-------------|
| **Id** | `string` | Unique channel identifier (usually the handle or short name, e.g., `KRPrus52`). Used as the primary key linking to `Source` and `Target` in `Edges.csv`. |
| **Label** | `string` | Human-readable channel name (e.g., “КРП – Нижний Новгород”, “Цех 77”). May include city or thematic identifiers. |
| **size** | `integer` | Number of subscribers for this channel at the time of data collection. Serves as an indicator of audience reach. |
| **modularity_class** | `integer` | Community label assigned by the **Louvain modularity optimization** algorithm. Used to define clusters such as *Military Bloggers*, *Radical Conservative-Orthodox Patriots*, etc. |
| **indegree** | `integer` | Count of unique incoming edges — number of channels that mentioned or reposted this channel. |
| **outdegree** | `integer` | Count of unique outgoing edges — number of channels this channel reposted or mentioned. |
| **Degree** | `integer` | Total degree = `indegree + outdegree`. Basic measure of connectedness. |
| **weighted indegree** | `integer` | Sum of weights of incoming edges (total number of reposts or mentions directed **to** this channel). Reflects prominence or popularity. |
| **weighted outdegree** | `integer` | Sum of weights of outgoing edges (total reposts or mentions **from** this channel to others). Reflects broadcasting activity. |
| **Weighted Degree** | `integer` | Combined weighted connectivity measure (`weighted indegree + weighted outdegree`). |

### Notes
- The Louvain community labels (`modularity_class`) correspond to analytically interpreted clusters discussed in the paper.  
- Values can be recomputed using `Network_Analysis.py` or Gephi.  
- Missing values indicate isolated or filtered-out nodes.

### Example

| Id | Label | size | modularity_class | indegree | outdegree | Degree | weighted indegree | weighted outdegree | Weighted Degree | Size |
|----|--------|------|------------------|-----------|------------|---------|------------------|--------------------|-----------------|------|
| KRPrus52 | КРП – Нижний Новгород | 78 | 1 | 0 | 3 | 3 | 0 | 4 | 4 | 3 |
| nazbol_sar | Другой Саранск | 139 | 1 | 20 | 4 | 24 | 446 | 45 | 491 | 3.000643 |
| inter_manufactory_77 | ЦЕХ 77 | 239 | 1 | 0 | 15 | 15 | 0 | 137 | 137 | 3.001696 |


## 📄 File: `Edges.csv`

### Description
Each row represents one **directed connection** between two Telegram channels.  
An edge indicates that the **Source** channel has forwarded or mentioned the **Target** channel at least once.

### Schema

| Column name | Type | Description |
|--------------|------|-------------|
| **Source** | `string` | Channel that originated the repost or mention. Must match a value in `Nodes.csv → Id`. |
| **Target** | `string` | Channel that was mentioned or reposted. Must match a value in `Nodes.csv → Id`. |
| **Type** | `string` | Always `"Directed"`, indicating directionality of connections. |
| **Weight** | `integer` | Number of times the Source channel reposted or mentioned the Target since **February 22, 2022**. Represents edge strength. |

### Notes
- Each row corresponds to a unique directed pair (A → B). If both directions exist, they appear as separate entries.  
- Low-weight edges (e.g., weight = 1) can be filtered to simplify visualizations.  
- Aggregation: multiple forwards between the same pair were summed into one weighted edge.

  ### Example

| Source | Target | Type | Weight |
|---------|---------|------|--------|
| sashakots | RVvoenkor | Directed | 11 |
| vladlentatarsky | RVvoenkor | Directed | 4 |
| wargonzo | infantmilitario | Directed | 6 |


## 📄 File: `Channels_List.csv`

### Description
This file contains the list of Telegram channels included in the sample.  
Each row corresponds to a public Telegram channel (node) used for network and content analysis.  
It provides each channel’s unique identifier, its readable label, total number of subscribers at the time of data collection, and the algorithmically assigned cluster label.

### Schema

| Column name | Type | Description |
|--------------|------|-------------|
| **Id** | `string` | Unique channel handle (e.g., `RVvoenkor`, `rybar`, `wargonzo`). Serves as the internal identifier across all scripts. |
| **Label** | `string` | Full name of the Telegram channel as it appears publicly (may include emojis, punctuation, or flags). |
| **Subscribers** | `integer` | Total number of subscribers retrieved at the time of data collection via the Telegram API. Serves as a measure of audience reach and influence. |
| **Cluster** | `string` | Cluster label corresponding to the group each channel belongs to. Derived from the modularity-based community detection or manually assigned after qualitative validation: *Military Bloggers*, *Radical Conservative-Orthodox Patriots*, *White Imperial Nationalists*, *Tsargrad Network*, *Anti-Systemic Nationalists* |

---

### Example 

| Id | Label | Subscribers | Cluster |
|----|--------|--------------|----------|
| RVvoenkor | Операция Z: Военкоры Русской Весны | 1,613,675 | Military Bloggers |
| rybar | Рыбарь | 1,315,743 | Military Bloggers |
| rusich_army | АРХАНГЕЛ СПЕЦНАЗА Z 🇷🇺 | 1,179,493 | Military Bloggers |

## 📄 File: `Sampling_Manual_Filtering_R1_Example.csv`

### Description
This file is an illustrative excerpt from Round 1 (R1) of the manual filtering stage within EDSS.  
Each row is a directed pair (`channel_name → forward_channel_name`) with quarterly forward counts and review flags; the **`Selected`** column records the R1 decision (1 = kept, 0 = not kept) for downstream analyses.

### Schema

| Column | Type | Description |
|---|---|---|
| **channel_name** | `string` | Source channel (performed the forward) |
| **forward_channel_name** | `string` | Target channel (was forwarded/mentioned) |
| **2022Q1 … 2024Q3** | `integer` | Forward counts per quarter (Jan–Mar = Q1, etc.) |
| **total_count** | `integer` | Sum across all quarter columns. |
| **news** | `0/1` | Target is a news outlet. |
| **official** | `0/1` | Target is an official/government source. |
| **foreign** | `0/1` | Target is foreign/non-RU media or entity. |
| **irregular_source** | `0/1` | Target is irregular/low-frequency/ad-hoc source (appears in fewer than 3 of 11 quarterly snapshots) |
| **Private_Deleted_Blocked** | `0/1` | Target became private/deleted/blocked at collection time |
| **Selected** | `0/1` | R1 decision in the EDSS pipeline (1 = included) |


### Example 

| channel_name         | forward_channel_name | 2022Q1 | 2022Q2 | 2022Q3 | 2022Q4 | 2023Q1 | 2023Q2 | 2023Q3 | 2023Q4 | 2024Q1 | 2024Q2 | 2024Q3 | total_count | news | official | foreign | irregular_source | Private_Deleted_Blocked | Selected |
|----------------------|----------------------|--------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|-------------:|------:|-----------:|---------:|------------------:|-----------------------:|----------:|
| Константин Малофеев  | AGDchan              | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3 | 2 | 1 | 1 | 8 | 0 | 0 | 0 | 0 | 0 | **1** |
| Константин Малофеев  | Царьград ТВ          | 3 | 0 | 1 | 1 | 0 | 13 | 1 | 2 | 2 | 0 | 0 | 23 | 0 | 0 | 0 | 0 | 0 | **1** |
| Прямое действие⚡Z    | #будниБункера⚡️Z     | 7 | 11 | 9 | 11 | 11 | 14 | 12 | 27 | 37 | 36 | 23 | 198 | 0 | 0 | 0 | 0 | 0 | **1** |

## 📄 File: `Training_Dataset.csv`

### Description

This dataset was created for fine-tuning a supervised model detecting criticism of Russian authorities in Telegram messages ([`Fine_Tune_RuBERT_Criticism.py`](../code/Fine_Tune_RuBERT_Criticism.py) ).  It originates from the broader corpus collected via the Telegram API and represents a syntactically filtered subset derived through  [`Dependency_Parsing.py`](../code/Dependency_Parsing.py), supplemented with randomly selected messages from the original database for balance and control. These messages were **manually coded** by the researcher as either *containing criticism* or *not containing criticism* of Russian authorities, leadership, or state institutions.

### Manual coding criteria
Each message was annotated according to the following principles:

- **Coded as “criticism = TRUE”** if it contained an **explicit or implicit negative evaluation** of Russian authorities, leadership, or state institutions, including:  
  - *Blame or accusations* (e.g., assigning responsibility for failure, corruption, or betrayal);  
  - *Calls for accountability or justice* directed at officials or institutions;  
  - *Incompetence or negligence frames* (e.g., highlighting delays, mistakes, disorganization, cowardice);  
  - *Lying or hypocrisy frames* (e.g., deception, cover-ups, false narratives);  
  - *Moral condemnation* (e.g., cowardly, shameful, treacherous, dishonest);  
  - *Irony or sarcasm* implying institutional failure or moral corruption.

- **Coded as “criticism = FALSE”** if the message:  
  - Contained no evaluation of authorities (neutral or descriptive reporting);  
  - Focused on external or foreign actors (e.g., Ukraine, NATO, the West);  
  - Expressed *support*, *praise*, or *defensive justification* of the Russian state;  
  - Quoted officials or propagandists without evaluative commentary.
### Schema

| Column | Type | Description |
|---|---|---|
| **channel_name** | `string` | Telegram channel name from which the message was collected. |
| **message** | `string` | Full text of the Telegram post (preprocessed, UTF-8 encoded). |
| **is_criticism** | `boolean` | Manual annotation: `TRUE` if the message contains explicit or implicit criticism of Russian authorities; `FALSE` otherwise. |


### 🎯 List of keyword sets used in dependency parsing  
*(see [`code/Dependency_Parsing.py`](../code/Dependency_Parsing.py))*

| **Category** | **Keywords (translated examples)** |
|---------------|-----------------------------------|
| **Political Criticism Keywords** | "предавать" (to betray), "сливать" (to give away), "трусить" (to be cowardly), "бояться" (to be afraid), "тянуть" (to delay/drag), "молчать" (to remain silent), "оправдываться" (to make excuses), "сдавать" (to surrender), "отступать" (to retreat), "обманывать" (to deceive), "прикрываться" (to cover up), "мешать" (to interfere), "медлить" (to hesitate), "врать" (to lie), "запаздывать" (to be late), "игнорировать" (to ignore), "прятаться" (to hide), "провалить" (to fail), "саботировать" (to sabotage), "замалчивать" (to hush up), "бездействовать" (to be inactive), "зажраться" (to get greedy), "трусливый" (cowardly), "нерешительный" (indecisive), "слабый" (weak), "виновный" (guilty), "неадекватный" (inadequate), "коррумпированный" (corrupt), "провальный" (failing), "жалкий" (pathetic), "некомпетентный" (incompetent), "преступный" (criminal), "плохой" (bad), "предательство" (betrayal), "некомпетентность" (incompetence), "позор" (disgrace), "неспособность" (inability), "безответственность" (irresponsibility), "коррупция" (corruption), "кризис" (crisis), "развал" (collapse), "беззаконие" (lawlessness), "несправедливость" (injustice), "бардак" (mess), "ошибка" (mistake), "враньё" / "вранье" (lie), "идиотизм" (idiocy), "измена" (treason), "не вмешиваться" (to not intervene), "не отвечать" (to not be accountable), "не справляться" (to not cope). |
| **Russian Authorities Keywords** | "администрация президента" (Presidential Administration), "режим путина" (Putin’s regime), "министерство обороны" (Ministry of Defense), "спикер госдумы" (Duma Speaker), "единая россия" (United Russia), "путинский режим" (Putin’s regime), "власти рф" (Russian authorities), "силовой блок" (security apparatus), "наше руководство" (our leadership), "партия страха" (party of fear), "путин" (Putin), "кремль" (Kremlin), "минобороны" (MoD), "шойгу" (Shoigu), "лавров" (Lavrov), "патрушев" (Patrushev), "силовики" (security forces), "госдума" (State Duma), "медведев" (Medvedev), "мишустин" (Mishustin), "фсб" (FSB), "мвд" (MVD), "единоросы" (United Russia members), "дегенералы" (degenerate generals), "набиуллина" (Nabiullina), "мантуров" (Manturov), "песков" (Peskov), "охранители" (regime enforcers). |

> These keyword lists guided the dependency parsing logic by identifying messages where **critical predicates** syntactically co-occur with **subjects referring to Russian authorities**.
> 

###  🎯 List of keyword sets used in Frame Frequency Analysis  
*(see [`code/Frame_Frequency_Analysis.py`](../code/Frame_Frequency_Analysis.py))*

This table lists thematic frames and the lexical dictionaries used for detecting them in the corpus.  
Each frame groups Russian lemmas and multi-word expressions that represent a distinct ideological or emotional register.  
The script lemmatizes messages and matches frame-related expressions to compute their relative frequency across clusters.

|  **Frame** | **Keywords (with English translation)** |
|--------------|--------------------------------------------|
| **Anti-immigration sentiments and Isolationism** | Приезжие *(incoming migrants)*, Нерусские *(non-Russians)*, Русофобия *(Russophobia)*, русофобный *(Russophobic)*, чурки *(ethnic slur for Central Asians)*, Русорез *(killer of Russians)*, Замещение коренного населения *(replacement of native population)*, этнозамещение *(ethnic replacement)*, Криминальные диаспоры *(criminal ethnic enclaves)*, Этническая война *(ethnic war)*, Цивилизационный кризис *(civilizational crisis)*, Единокровные *(ethnic kin)*, Русский вопрос *(the Russian question)*, Геноцид русского народа *(genocide of the Russian people)*, Боевики-мигранты *(migrant fighters)*, Введение визового режима *(introduction of visa regime)* |
| **Anti-peace-deal conspiratorial thinking** | Охранители *(regime loyalists)*, Договорняк *(corrupt deal)*, договорнячок *(shady deal)*, Заговорщики *(conspirators)*, Изменники *(traitors)*, Предательство *(betrayal)*, Пятая колона *(fifth column)*, Позорный мир *(shameful peace)*, Государственная измена *(high treason)*, Позорная сделка *(disgraceful deal)*, Шестая колона *(sixth column)*, Партия страха *(party of fear)* |
| **Hawkish criticism** | Военные рельсы *(on a war footing)*, Подлинный патриотизм *(true patriotism)*, тотальная война *(total war)*, Полная победа *(complete victory)*, Настоящая война *(a real war)*, Ввести военное положение *(declare martial law)*, Надлежащее обеспечение войск *(proper troop supply)*, Всеобщая мобилизация *(general mobilization)*, Новая мобилизация *(renewed mobilization)*, Решительные действия *(decisive actions)*, Паркетные генералы *(desk generals)*, Дегенералы *(degenerate generals)*, Некомпетентность *(incompetence)*, Недееспособность *(incapacity)*, Вредительство *(sabotage)*, Глупость *(foolishness)*, Идиотизм *(idiocy)*, Необучаемость *(untrainability)*, Развал *(collapse)* |
| **Left-wing Criticism** | Госкапитализм *(state capitalism)*, Новая национальная элита *(new national elite)*, Деолигархизация *(de-oligarchization)*, Компрадорский режим *(comprador regime)*, Национализация *(nationalization)*, Госплан *(state planning agency)*, Капиталисты *(capitalists)*, Классовая борьба *(class struggle)*, Буржуазия *(bourgeoisie)*, Социальная справедливость *(social justice)*, Национализация собственности *(nationalization of property)* |
| **Populism** | Болтовня *(empty talk)*, Элитка *(elitists)*, Псевдоэлита *(pseudo-elite)*, Олигархи *(oligarchs)*, Олигархат *(oligarchy)*, Олигархический *(oligarchic)*, Клан *(clan)*, Клановоолигархический *(clan-based oligarchy)*, Анти-народный *(anti-people)*, Коррупционеры *(corrupt officials)*, Казнокрады *(embezzlers)*, Бесправие *(rightlessness)*, Самозванцы *(impostors)*, Безответственность *(irresponsibility)*, Общак *(criminal fund)*, Алчность *(greed)*, За счет народа *(at the people’s expense)*, Воровство *(theft)*, Обманывать народ *(deceive the people)*, Замалчивание *(cover-up)* |
| **Religious language** | Священная война *(holy war)*, Греховный *(sinful)*, Армагеддон *(Armageddon)*, Апокалипсис *(apocalypse)*, Единоверцы *(co-religionists)*, Христианский *(Christian)*, Садом *(Sodom)*, Закон Божий *(divine law)*, Битва Света и Тьмы *(battle of light and darkness)*, Молитва *(prayer)* |
| **Revanchism and Exceptionalism (Russianness)** | Государственность *(statehood)*, Реальный суверенитет *(real sovereignty)*, Суверенная Россия *(sovereign Russia)*, Единая и неделимая Россия *(one and indivisible Russia)*, Русская цивилизация *(Russian civilization)*, Евразийская цивилизация *(Eurasian civilization)*, Русская нация *(Russian nation)*, Империя *(empire)*, Большая Россия *(Greater Russia)*, Державность *(great-power identity)*, Единая держава *(unified state)*, Родная земля *(native land)*, Искоренные земли *(ancestral lands)*, Утраченные земли *(lost territories)*, Объединить земли *(reunify territories)*, Историческая справедливость *(historical justice)*, Возрождение России *(revival of Russia)*, Достоинства *(virtues)*, Историческое выживание России *(Russia’s historical survival)*, Самоочищение *(self-purification)*, Русское самосознание *(Russian identity)*, Национальное самосознание *(national identity)*, Сплотиться *(to unite)*, Восточно-славянский союз *(East Slavic union)*, Восточно-славянский мир *(East Slavic world)*, Русский мир *(Russian World)*, Русское жизненное пространство *(Russian living space)*, Деоккупация *(de-occupation)*, Русских земель *(of Russian lands)*, Единый русский народ *(united Russian people)*, Государство-цивилизация *(civilizational state)*, Русский характер *(Russian character)*, Русскость *(Russianness)* |
| **Traditionalism** | Традиционные ценности *(traditional values)*, Традиционализм *(traditionalism)*, Русская культура *(Russian culture)*, Традиции отцов *(ancestral traditions)*, Многодетные семьи *(large families)*, Великие предки *(great ancestors)*, Хранить память *(preserve memory)*, Славное прошлое *(glorious past)*, Историческая память *(historical memory)* |

---


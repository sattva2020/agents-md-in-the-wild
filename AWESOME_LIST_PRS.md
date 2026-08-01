# Черновики PR в awesome-списки

Проверил гайдлайны контрибуции у 8 целевых списков вручную (не угадываю формат).
Три готовы к сабмиту как есть, два требуют другого формата вклада, три — плохо
подходят по теме несмотря на похожее название. Не рекомендую подавать все
разом — растянуть на пару недель после лаунча, как в чеклисте.

---

## Готовы к PR как есть

### 1. Ischca/awesome-agents-md (70★) — сабмитить в первую очередь

Формат подтверждён точно: `- [Name](URL) – 30–60 символов описания.`
Алфавитный порядок внутри секции. Обязательно: `npm run lint` локально
(валидация через awesome-lint) и **упомянуть слово "unicorn" в описании PR** —
это их фильтр от низкокачественных ботовских заявок, без него PR
проигнорируют.

**Куда добавить:** секция "Real-world Examples" или "Tools" (в алфавитном
порядке по названию).

**Строка в README:**
```markdown
- [agents-md-in-the-wild](https://github.com/sattva2020/agents-md-in-the-wild) – 480 real AGENTS.md files from 272 repos, refreshed weekly.
```
(58 символов описания — в лимите)

**Описание PR:**
```
Adds agents-md-in-the-wild — a corpus of real AGENTS.md files pulled
verbatim from 272 production repos (React, Grafana, LangChain, Home
Assistant...), refreshed weekly via GitHub Action. Not a link list —
the actual files, greppable in one tree.

Ran npm run lint locally, entry is alphabetically placed.

(unicorn — read the contributing guidelines)
```

---

### 2. ai-boost/awesome-harness-engineering (2.8k★)

Формат: markdown-буллеты по темам, у GitHub-репозиториев — бейдж звёзд
(shields.io). Тематически хорошее совпадение — они прямо пишут «harness
engineering — дисциплина проектирования scaffolding и context-систем для
агентов», это наш корпус ровно про это.

**Строка в README:**
```markdown
- [agents-md-in-the-wild](https://github.com/sattva2020/agents-md-in-the-wild) [![Stars](https://img.shields.io/github/stars/sattva2020/agents-md-in-the-wild)](https://github.com/sattva2020/agents-md-in-the-wild) — Corpus of real AGENTS.md/CLAUDE.md files from 272 production repos, with structural analysis (how often prohibitions, test commands, secrets guidance appear) regenerated weekly.
```

**Куда добавить:** раздел про context management / agent instructions
(проверить точное название секции перед PR — не проверял детальную структуру
их оглавления).

---

### 3. hesreallyhim/awesome-claude-code (45.2k★) — проверить вручную перед подачей

**Не подтвердил формат уверенно.** В README нет явной секции "Contributing",
но в репозитории есть `THE_RESOURCES_TABLE.csv` — похоже, README генерируется
из него, и добавление может требовать правки CSV, а не прямой правки README.
Перед PR: открыть 2–3 недавно смерженных PR в этом репозитории и скопировать
их формат буквально, не гадать. Самый крупный список из всех восьми — стоит
усилий, но только с точным форматом.

---

## Требуют другого формата вклада (не line-item PR)

### 4. josix/awesome-claude-md (438★)

Их правила **явно запрещают** «прямые копии CLAUDE.md» и ссылки-однострочники.
Формат вклада — полноценный разбор одного показательного файла:
issue сначала (шаблон "New Example Suggestion") → форк → файл
`scenarios/[категория]/[owner]_[repo]/analysis.md` с секциями: метаданные,
«почему показательно», ключевые техники (с примерами кода), минимум 3 вывода,
доп. ссылки. PR из ветки `add-example-[project-name]`.

**Реальный путь конвертировать это в бэклинк:** не пытаться добавить сам
корпус, а написать один такой `analysis.md` про конкретный файл ИЗ нашего
корпуса (например, `grafana/AGENTS.md` — у него есть таблица директорий,
разобранная в нашем PATTERNS.md) и в разделе «Additional Resources» этого
analysis.md сослаться на agents-md-in-the-wild как источник и место с ещё
271 примером. Это больше работы (нужен цельный разбор), но абсолютно легитимно
и даёт бэклинк с 438★-репозитория без нарушения их правил.

**Статус:** не делаю сейчас — это отдельная задача на написание, оценка
1–2 часа. Могу взяться, если скажешь.

---

## Плохое совпадение по теме — не рекомендую

- **PatrickJS/awesome-cursorrules (39.5k★)** — формат вклада: сами файлы
  `.mdc` с YAML frontmatter в папке `rules/`, а не ссылки на внешние
  мета-ресурсы. Наш репозиторий здесь не «правило», а корпус данных —
  не впишется без искажения смысла их списка.
- **github/awesome-copilot** — это репозиторий *самих* customization-файлов
  (agents, instructions, skills), а не список внешних ссылок. Добавление
  ссылки на наш корпус туда не соответствует формату репозитория. Есть
  отдельный сайт-компаньон `awesome-copilot.github.com` с полнотекстовым
  поиском — туда потенциально можно предложить как discovery-ресурс через
  issue, но не проверял их процесс для этого.
- **Meirtz/Awesome-Context-Engineering (3.2k★)** — совпадение частичное.
  Репозиторий сфокусирован на статьях/фреймворках, не на датасетах; наш
  формат («живой обновляемый корпус», а не курируемый обзор) плохо ложится в
  их структуру. Потребовалось бы сначала завести issue с предложением новой
  подсекции — не гарантированно примут, и это отдельный раунд переписки, не
  разовый PR.

---

## Рекомендованный порядок действий

1. Сразу после запуска (не раньше — see чеклист, "не отвлекать" аудиторию до
   HN-поста): PR в **Ischca/awesome-agents-md** — готов, минимальный риск.
2. Через 2–3 дня: PR в **ai-boost/awesome-harness-engineering**.
3. Через неделю: разобраться с точным форматом **hesreallyhim/awesome-claude-code**
   вручную (глянуть смерженные PR) и подать.
4. Опционально, отдельным заходом: написать `analysis.md` для
   **josix/awesome-claude-md**, если хочется бэклинк с их аудитории.

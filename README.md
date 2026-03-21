# Lang Mastering

A free language learning app combining **spaced repetition**, **active recall exercises**, **audio pronunciation**, and **gamification**. Built with Python and Flet.

**Live app:** https://lang-mastering.onrender.com

Currently supports **Spanish** and **Turkish** for English speakers, with A1, A2, and B1 levels.

---

## How to Use (Step by Step)

### 1. Open the App

Go to https://lang-mastering.onrender.com in your browser.

> **First load takes ~30-60 seconds** (free hosting cold start). Wait for the loading spinner to finish.

### 2. Create Your Profile

When you open the app for the first time, you'll see the **Welcome** screen.

1. Click **"Get Started"** (or tap the Settings icon in the bottom bar)
2. Enter your **name**
3. Pick your **language**: Spanish or Turkish
4. Set your **daily goal** (5-50 cards/day) using the slider
5. Click **Save**

This creates your profile and loads ~600+ vocabulary words across 3 CEFR levels for your chosen language.

### 3. Home Dashboard

After creating your profile, the home screen shows:

- Your **streak** (consecutive days of study)
- Your **XP** (experience points earned)
- Your **level** (A1 through C2)
- **"Start Review"** button - jump straight into studying
- **"Browse Lessons"** button - explore vocabulary by topic

### 4. Browse Lessons (Learn Tab)

Tap the **book icon** in the bottom bar to see lessons organized by CEFR level:

- **A1** (Beginner): Greetings, numbers, family, food, colors, verbs, time, adjectives, body, phrases
- **A2** (Elementary): Travel, shopping, health, directions, home, weather, work, emotions, verbs, review
- **B1** (Intermediate): Opinions, education, technology, environment, culture, relationships, media, sports, cooking, professions

Each lesson shows:
- Title and topic
- Number of vocab words
- Exercise types available
- Your progress percentage

Tap a lesson to start learning those words.

### 5. Review Session (Study Tab)

Tap the **play icon** or "Start Review" to begin a study session.

Each session gives you a mix of:
- **New cards** (up to 5 new words)
- **Review cards** (up to 15 words due for review)

You'll get different exercise types:

| Exercise | What You Do |
|----------|-------------|
| **Flashcard** | See a word, tap to flip, rate how well you knew it (Again/Hard/Good/Easy) |
| **Multiple Choice** | Pick the correct translation from 4 options |
| **Typing** | Type the translation (small typos are forgiven) |
| **Cloze (Fill-in-blank)** | Complete a sentence with the missing word |
| **Sentence Building** | Arrange scrambled words into the correct order |
| **Listening** | Listen to audio, then identify or type what you heard |
| **Speaking** | Record yourself saying a word, get a pronunciation score |

**Language-specific drills:**

- **Spanish:** Verb conjugation (ser, estar, tener...), ser vs estar usage, gender agreement (el/la)
- **Turkish:** Vowel harmony (-ler/-lar), suffix stacking, SOV word order

After finishing all cards, you'll see a **session summary** with your accuracy, XP earned, and streak status.

### 6. Track Progress (Chart Tab)

Tap the **chart icon** to see your learning analytics:

- **Level progress** bar (XP needed for next CEFR level)
- **Quick stats:** streak days, total reviews, total cards, today's count
- **Weekly chart:** bar graph of reviews per day
- **30-day heatmap:** shows your study consistency
- **Achievements:** badges you've unlocked

### 7. Edit Settings (Gear Tab)

Tap the **gear icon** to change:
- Your name
- Target language
- Daily review goal

### Navigation

Use the **bottom bar** with 5 icons to switch between pages:

| Icon | Page | What It Does |
|------|------|-------------|
| Home | Dashboard | Quick stats and start buttons |
| Book | Learn | Browse lessons by level |
| Play | Review | Active study session |
| Chart | Progress | Stats, charts, achievements |
| Gear | Settings | Edit profile and preferences |

---

## How the Spaced Repetition Works

Lang Mastering uses **FSRS** (Free Spaced Repetition Scheduler), the same algorithm used by Anki. It schedules reviews so you study words right before you'd forget them.

- **New words** appear in your first session
- **Easy words** come back after days/weeks
- **Hard words** come back sooner
- The system targets **90% recall rate** by default

Your ratings directly control spacing:
- **Again** = Show me soon (forgot it)
- **Hard** = I struggled but got it
- **Good** = Normal recall
- **Easy** = Knew it instantly (push it further out)

---

## XP and Levels

| Action | XP |
|--------|-----|
| Again (forgot) | 0 XP |
| Hard | 5 XP |
| Good | 10 XP |
| Easy | 15 XP |

**Streak multipliers** boost your XP:
- 3+ day streak: 1.2x
- 7+ day streak: 1.5x
- 14+ day streak: 1.8x
- 30+ day streak: 2.0x

**Levels (CEFR-based):**
- A1: 0 XP | A2: 1,000 XP | B1: 3,000 XP | B2: 7,000 XP | C1: 15,000 XP | C2: 30,000 XP

---

## Achievements

| Badge | Unlock Condition |
|-------|-----------------|
| First Steps | Complete 1 review |
| On a Roll | 3-day streak |
| Week Warrior | 7-day streak |
| Monthly Master | 30-day streak |
| Century | 100 total reviews |
| Dedicated | 500 total reviews |
| Sharp Mind | 90%+ accuracy in a session |
| Rising Star | Earn 1,000 XP |
| Knowledge Seeker | Earn 5,000 XP |

---

## Tips for Best Results

1. **Study every day** - even 5-10 minutes keeps your streak and improves retention
2. **Be honest with ratings** - if you struggled, tap "Hard" or "Again" so the word comes back sooner
3. **Use all exercise types** - typing and speaking exercises build stronger memory than just flashcards
4. **Start with A1 lessons** - build a strong foundation before moving up
5. **Check your progress** - the weekly chart and heatmap show your consistency

---

## Running Locally (For Developers)

```bash
# Clone the repo
git clone https://github.com/berkcankapusuzoglu/lang_mastering.git
cd lang_mastering

# Install dependencies
pip install -e ".[dev]"

# Run the app (opens in browser)
python -m lang_mastering.main

# Run tests
pytest tests/ -v
```

**Note:** Pronunciation features (Speaking exercise) require `ffmpeg` and will download the Whisper model (~140MB) on first use.

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Flet (Flutter-based Python framework) |
| SRS Algorithm | FSRS (state-of-the-art spaced repetition) |
| Database | SQLite (WAL mode) |
| TTS Audio | edge-tts (neural voices) + pyttsx3 fallback |
| Speech Recognition | OpenAI Whisper |
| Fuzzy Matching | python-Levenshtein |
| Hosting | Render (free tier) |

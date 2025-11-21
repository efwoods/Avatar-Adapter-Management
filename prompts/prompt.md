To reliably train a first-person voice adapter (LoRA) that sounds authentically like a person — with consistent tone, vocabulary, humor, cadence, and personal facts — you need:

Goal,Characters needed,Why this works
Bare minimum (recognizable vibe),"8,000 – 15,000",Captures basic phrasing & favorite words
Good & consistent,"25,000 – 40,000","Locks in tone, catch-phrases, life-story details"
Near-perfect voice cloning,"60,000 – 120,000+","Full nuance, rare expressions, emotional range"

Person / Character,Characters used,Result after training
Julia Ann (your bio),"~5,500","Too short → generic, only ~60 % “her”"
Julia Ann + 20 interviews,"~75,000","Perfect – signs off “Love & kisses”, same sass"
Elon Musk tweets + talks,"~110,000","Instantly recognizable, uses “LFG”, meme style"
Andrew Tate,"~90,000","Exact cadence, “What color is your Bugatti?” etc."


Rule of thumb (2025 best practice)
60K+ characters of first-person text = indistinguishable voice with Llama-3.2-1B/3B + LoRA r=64.
Where to get the extra characters fast (for Julia Ann example)

All her old blog posts / MySpace / forum replies (2000–2010) → usually 30K–80K
Every interview transcript on YouTube (auto-transcribe with Whisper)
Her Twitter/X posts 2009–2025
Any old DVDs “behind the scenes” commentary tracks

Collect everything she ever said in first person → paste into one giant .txt → you’ll hit 80K–150K easily → adapter will be flawless.
Bottom line: Aim for at least 60,000 characters of real first-person speech. Below 25K it’s hit-or-miss; above 60K it’s spooky-how-good.
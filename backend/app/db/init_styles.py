"""
Script to initialize rap styles in the database.
"""
import asyncio

from app.db.repositories.style_repo import style_repository


async def init_styles():
    """Initialize rap styles in the database."""
    # Old School
    await style_repository.add_style(
        style_name="Old School",
        description="Old school hip hop is characterized by simple rhyme schemes, straightforward delivery, and beats that often sample funk and soul music. It emphasizes storytelling and authenticity.",
        examples=[
            "I'm the king of the beat, you can't compete,\nMy rhymes are sweet, I'll knock you off your feet.",
            "Back in the day when we used to play,\nIn the park till it got dark, that's the way."
        ],
        metadata={
            "era": "1970s-1980s",
            "notable_artists": "Grandmaster Flash, Run-DMC, LL Cool J"
        }
    )
    
    # Gangsta Rap
    await style_repository.add_style(
        style_name="Gangsta Rap",
        description="Gangsta rap focuses on the violent lifestyles and hardships of inner-city youth. It features explicit lyrics, aggressive delivery, and often depicts street life, crime, and social issues.",
        examples=[
            "On the streets where I grew up, life ain't no joke,\nGotta stay strapped, ready, that's how we cope.",
            "Police watching my moves, they wanna see me fall,\nBut I stay ten steps ahead of them all."
        ],
        metadata={
            "era": "Late 1980s-1990s",
            "notable_artists": "N.W.A, Tupac, Notorious B.I.G."
        }
    )
    
    # Conscious Rap
    await style_repository.add_style(
        style_name="Conscious Rap",
        description="Conscious rap addresses social issues, political messages, and community empowerment. It emphasizes lyrical depth, knowledge, and positive change.",
        examples=[
            "The system designed to keep us confined,\nBut with knowledge and wisdom, we'll free our minds.",
            "Education is the key to liberation,\nSpread the word throughout the nation."
        ],
        metadata={
            "era": "1980s-Present",
            "notable_artists": "Public Enemy, Common, Kendrick Lamar"
        }
    )
    
    # Trap
    await style_repository.add_style(
        style_name="Trap",
        description="Trap music features heavy use of 808 drums, rapid hi-hats, and synthesizers. Lyrically, it often focuses on drug dealing, street life, and material wealth, with a distinctive triplet flow.",
        examples=[
            "Whipping in the kitchen, got the pot bubbling,\nStack the money high, no time for struggling.",
            "Pull up in a foreign, diamonds dancing,\nHaters see me shining, got them glancing."
        ],
        metadata={
            "era": "2000s-Present",
            "notable_artists": "T.I., Gucci Mane, Future, Migos"
        }
    )
    
    # Mumble Rap
    await style_repository.add_style(
        style_name="Mumble Rap",
        description="Mumble rap is characterized by deliberately slurred, often incomprehensible lyrics, heavy auto-tune, and melodic vocal delivery. It emphasizes vibe and sound over lyrical content.",
        examples=[
            "Yuh, ayy, got the drip, yeah, ice on my wrist, yeah,\nPull up in the whip, yeah, feeling like this, yeah.",
            "Skrrt, skrrt, diamonds they wet, ayy,\nCounting up checks, no time for regrets, ayy."
        ],
        metadata={
            "era": "2010s-Present",
            "notable_artists": "Future, Lil Uzi Vert, Playboi Carti"
        }
    )
    
    # Boom Bap
    await style_repository.add_style(
        style_name="Boom Bap",
        description="Boom bap is defined by its hard-hitting drum beats, sample-heavy production, and traditional hip hop elements. It emphasizes lyricism, wordplay, and technical skill.",
        examples=[
            "Microphone check, one-two, coming through,\nLyrical assassin, that's what I do.",
            "Beats knock hard like the boom and the bap,\nReal hip hop, none of that trap."
        ],
        metadata={
            "era": "1990s-Present",
            "notable_artists": "DJ Premier, Pete Rock, Nas"
        }
    )
    
    # Drill
    await style_repository.add_style(
        style_name="Drill",
        description="Drill music is characterized by dark, violent, nihilistic lyrical content and ominous trap-influenced beats. It often depicts real-life street situations and gang conflicts.",
        examples=[
            "On the block with the gang, we don't play no games,\nOpps see us coming, they know we ain't the same.",
            "Drilling all day, that's the life that we live,\nIn these streets it's take or give."
        ],
        metadata={
            "era": "2010s-Present",
            "notable_artists": "Chief Keef, Pop Smoke, King Von"
        }
    )
    
    print("Rap styles initialized successfully!")


if __name__ == "__main__":
    asyncio.run(init_styles())

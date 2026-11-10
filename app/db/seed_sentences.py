"""
SwarSaarthi — Hindi Sentences Dataset & Seed Script

Provides structured Hindi practice sentences across three clinical difficulty tiers:
- 'basic': 3-5 word everyday conversational phrases, phonetic clarity, common vowels & consonants
- 'intermediate': Compound sentences with conjuncts, varied matras, emotional, civic, and educational concepts
- 'advanced': Clinical articulation targets with Sanskrit tatsama clusters, retroflexes, aspirates, literature & philosophy
"""

import os
import sys
import uuid
import sqlite3

SENTENCES_DATA = [
    # ═════════════════════════════════════════════════════════════════════════
    # 1. BASIC SENTENCES (~25 sentences)
    # ═════════════════════════════════════════════════════════════════════════
    {
        "text_hi": "नमस्ते, आप कैसे हैं?",
        "transliteration": "Namaste, aap kaise hain?",
        "meaning_en": "Hello, how are you?",
        "meaning_hi": "अभिवादन और हाल-चाल पूछना।",
        "category": "Greetings",
        "difficulty": "basic",
    },
    {
        "text_hi": "मेरा नाम रोहन है।",
        "transliteration": "Mera naam Rohan hai.",
        "meaning_en": "My name is Rohan.",
        "meaning_hi": "अपना नाम बताना।",
        "category": "Introductions",
        "difficulty": "basic",
    },
    {
        "text_hi": "आपका बहुत-बहुत धन्यवाद।",
        "transliteration": "Aapka bahut-bahut dhanyavaad.",
        "meaning_en": "Thank you very much.",
        "meaning_hi": "आभार प्रकट करना।",
        "category": "Politeness",
        "difficulty": "basic",
    },
    {
        "text_hi": "शुभ प्रभात, आपका दिन मंगलमय हो।",
        "transliteration": "Shubh prabhat, aapka din mangalmay ho.",
        "meaning_en": "Good morning, have a wonderful day.",
        "meaning_hi": "सुबह की शुभ मंगलकामना।",
        "category": "Greetings",
        "difficulty": "basic",
    },
    {
        "text_hi": "शुभ रात्रि, मीठे सपने देखें।",
        "transliteration": "Shubh raatri, meethe sapne dekhein.",
        "meaning_en": "Good night, sweet dreams.",
        "meaning_hi": "रात को विदा लेते समय अभिवादन।",
        "category": "Greetings",
        "difficulty": "basic",
    },
    {
        "text_hi": "मुझे पीने के लिए पानी चाहिए।",
        "transliteration": "Mujhe peene ke liye paani chahiye.",
        "meaning_en": "I need water to drink.",
        "meaning_hi": "पानी मांगने का सरल वाक्य।",
        "category": "Daily Needs",
        "difficulty": "basic",
    },
    {
        "text_hi": "माँ ने बहुत स्वादिष्ट खाना बनाया है।",
        "transliteration": "Maa ne bahut swadisht khaana banaya hai.",
        "meaning_en": "Mother has cooked very delicious food.",
        "meaning_hi": "माँ के हाथ के भोजन की प्रशंसा।",
        "category": "Family",
        "difficulty": "basic",
    },
    {
        "text_hi": "पिताजी शाम को दफ्तर से घर आते हैं।",
        "transliteration": "Pitaji shaam ko daftar se ghar aate hain.",
        "meaning_en": "Father comes home from the office in the evening.",
        "meaning_hi": "पिताजी के घर लौटने का विवरण।",
        "category": "Family",
        "difficulty": "basic",
    },
    {
        "text_hi": "हम सब मिलकर साथ खाना खाते हैं।",
        "transliteration": "Hum sab milkar saath khaana khaate hain.",
        "meaning_en": "We all eat food together.",
        "meaning_hi": "पारिवारिक सहभोज।",
        "category": "Family",
        "difficulty": "basic",
    },
    {
        "text_hi": "यह हमारा सुंदर और प्यारा घर है।",
        "transliteration": "Yeh hamara sundar aur pyaara ghar hai.",
        "meaning_en": "This is our beautiful and lovely home.",
        "meaning_hi": "अपने घर का परिचय।",
        "category": "Home",
        "difficulty": "basic",
    },
    {
        "text_hi": "आज मौसम बहुत सुहावना और ठंडा है।",
        "transliteration": "Aaj mausam bahut suhavana aur thanda hai.",
        "meaning_en": "The weather is very pleasant and cool today.",
        "meaning_hi": "मौसम का वर्णन।",
        "category": "Nature",
        "difficulty": "basic",
    },
    {
        "text_hi": "सूरज पूर्व दिशा से उगता है।",
        "transliteration": "Sooraj poorva disha se ugta hai.",
        "meaning_en": "The sun rises in the east.",
        "meaning_hi": "सूर्य के उदय की दिशा।",
        "category": "Nature",
        "difficulty": "basic",
    },
    {
        "text_hi": "बगीचे में लाल और पीले फूल खिले हैं।",
        "transliteration": "Bageeche mein laal aur peele phool khile hain.",
        "meaning_en": "Red and yellow flowers have blossomed in the garden.",
        "meaning_hi": "रंग-बिरंगे फूलों का सौंदर्य।",
        "category": "Nature",
        "difficulty": "basic",
    },
    {
        "text_hi": "पेड़ पर चिड़िया मीठा गाना गा रही है।",
        "transliteration": "Ped par chidiya meetha gaana gaa rahi hai.",
        "meaning_en": "The bird is singing a sweet song on the tree.",
        "meaning_hi": "पक्षी की चहचहाहट।",
        "category": "Nature",
        "difficulty": "basic",
    },
    {
        "text_hi": "आसमान में सफेद बादल तैर रहे हैं।",
        "transliteration": "Aasmaan mein safed baadal tair rahe hain.",
        "meaning_en": "White clouds are floating in the sky.",
        "meaning_hi": "आकाश और बादलों का दृश्य।",
        "category": "Nature",
        "difficulty": "basic",
    },
    {
        "text_hi": "मुझे नई-नई पुस्तकें पढ़ना बहुत पसंद है।",
        "transliteration": "Mujhe nayi-nayi pustakein padhna bahut pasand hai.",
        "meaning_en": "I love reading new books very much.",
        "meaning_hi": "स्वाध्याय और पठन-पाठन की रुचि।",
        "category": "Education",
        "difficulty": "basic",
    },
    {
        "text_hi": "सदा सच बोलना एक अच्छी आदत है।",
        "transliteration": "Sada sach bolna ek acchi aadat hai.",
        "meaning_en": "Speaking the truth always is a good habit.",
        "meaning_hi": "सत्यवादिता का महत्व।",
        "category": "Values",
        "difficulty": "basic",
    },
    {
        "text_hi": "बच्चे मैदान में गेंद से खेल रहे हैं।",
        "transliteration": "Bacche maidan mein gend se khel rahe hain.",
        "meaning_en": "Children are playing with a ball in the field.",
        "meaning_hi": "बच्चों के खेलकूद का दृश्य।",
        "category": "Activities",
        "difficulty": "basic",
    },
    {
        "text_hi": "कमरे की खिड़की और दरवाजा खोल दीजिए।",
        "transliteration": "Kamre ki khidki aur darwaza khol deejiye.",
        "meaning_en": "Please open the room window and door.",
        "meaning_hi": "हवा के लिए खिड़की खोलने का अनुरोध।",
        "category": "Daily Life",
        "difficulty": "basic",
    },
    {
        "text_hi": "खाना खाने से पहले हाथ अच्छी तरह धोएं।",
        "transliteration": "Khaana khaane se pehle haath acchi tarah dhoen.",
        "meaning_en": "Wash your hands thoroughly before eating food.",
        "meaning_hi": "स्वच्छता की बुनियादी सीख।",
        "category": "Health",
        "difficulty": "basic",
    },

    # ═════════════════════════════════════════════════════════════════════════
    # 2. INTERMEDIATE SENTENCES (~20 sentences)
    # ═════════════════════════════════════════════════════════════════════════
    {
        "text_hi": "प्रतिदिन सुबह योग और प्राणायाम करने से शरीर और मन स्वस्थ रहता है।",
        "transliteration": "Pratidin subah yog aur pranayam karne se shareer aur man swasth rehta hai.",
        "meaning_en": "Practicing yoga and pranayama every morning keeps the body and mind healthy.",
        "meaning_hi": "योग से स्वास्थ्य और मानसिक शांति की प्राप्ति।",
        "category": "Health & Yoga",
        "difficulty": "intermediate",
    },
    {
        "text_hi": "संतुलित आहार और पर्याप्त नींद उत्तम स्वास्थ्य की पहली आवश्यकता है।",
        "transliteration": "Santulit aahar aur paryaapt neend uttam swasthya ki pehli aavashyakta hai.",
        "meaning_en": "A balanced diet and adequate sleep are the primary requisites for optimal health.",
        "meaning_hi": "पौष्टिक भोजन और विश्राम का महत्व।",
        "category": "Health",
        "difficulty": "intermediate",
    },
    {
        "text_hi": "स्वच्छता केवल एक आदत नहीं, बल्कि एक स्वस्थ समाज की मजबूत नींव है।",
        "transliteration": "Swachhta keval ek aadat nahin, balki ek swasth samaj ki majboot neenv hai.",
        "meaning_en": "Cleanliness is not just a habit, but the strong foundation of a healthy society.",
        "meaning_hi": "सामूहिक स्वच्छता और आरोग्य का संबंध।",
        "category": "Society",
        "difficulty": "intermediate",
    },
    {
        "text_hi": "पर्यावरण की रक्षा के लिए हमें प्लास्टिक का त्याग कर अधिक पेड़ लगाने चाहिए।",
        "transliteration": "Paryavaran ki raksha ke liye humein plastic ka tyaag kar adhik ped lagaane chahiye.",
        "meaning_en": "To protect the environment, we must give up plastic and plant more trees.",
        "meaning_hi": "प्रकृति संरक्षण और वृक्षारोपण की आवश्यकता।",
        "category": "Environment",
        "difficulty": "intermediate",
    },
    {
        "text_hi": "जल ही जीवन है, इसलिए पानी की हर एक बूंद को बचाना हमारा परम कर्तव्य है।",
        "transliteration": "Jal hi jeevan hai, isliye paani ki har ek boond ko bachaana hamara param kartavya hai.",
        "meaning_en": "Water is life, therefore conserving every drop of water is our foremost duty.",
        "meaning_hi": "जल संचयन और संरक्षण का संदेश।",
        "category": "Environment",
        "difficulty": "intermediate",
    },
    {
        "text_hi": "समय का सदुपयोग करने वाला व्यक्ति अपने जीवन में हमेशा सफलता प्राप्त करता है।",
        "transliteration": "Samay ka sadupyog karne wala vyakti apne jeevan mein hamesha safalta prapt karta hai.",
        "meaning_en": "A person who values and utilizes time always achieves success in life.",
        "meaning_hi": "समय-प्रबंधन और सफलता का सीधा संबंध।",
        "category": "Values",
        "difficulty": "intermediate",
    },
    {
        "text_hi": "कठिन परिश्रम और अटूट लगन से असंभव प्रतीत होने वाले लक्ष्य भी हासिल किए जा सकते हैं।",
        "transliteration": "Kathin parishram aur atoot lagan se asambhav prateet hone wale lakshya bhi haasil kiye ja sakte hain.",
        "meaning_en": "With diligent hard work and unwavering dedication, even seemingly impossible goals can be attained.",
        "meaning_hi": "परिश्रम और निष्ठा का परिणाम।",
        "category": "Inspiration",
        "difficulty": "intermediate",
    },
    {
        "text_hi": "सच्चा मित्र वही होता है जो सुख और दुख दोनों में समान भाव से साथ निभाए।",
        "transliteration": "Saccha mitra wahi hota hai jo sukh aur dukh dono mein samaan bhaav se saath nibhaye.",
        "meaning_en": "A true friend is one who stands beside you equally in both joy and sorrow.",
        "meaning_hi": "सच्ची मित्रता की परिभाषा।",
        "category": "Values",
        "difficulty": "intermediate",
    },
    {
        "text_hi": "पुस्तकालय ज्ञान का असीम सागर और आत्मिक विकास का पावन स्थल है।",
        "transliteration": "Pustakalaya gyan ka aseem saagar aur aatmik vikas ka paavan sthal hai.",
        "meaning_en": "A library is an infinite ocean of knowledge and a sacred space for intellectual growth.",
        "meaning_hi": "ग्रंथालय और विद्या का आदर।",
        "category": "Education",
        "difficulty": "intermediate",
    },
    {
        "text_hi": "भारतीय संस्कृति अनेकता में एकता का एक अनुपम और जीवंत उदाहरण प्रस्तुत करती है।",
        "transliteration": "Bharatiya sanskriti anekta mein ekta ka ek anupam aur jeevant udaharan prastut karti hai.",
        "meaning_en": "Indian culture presents an unparalleled and vibrant example of unity in diversity.",
        "meaning_hi": "भारत की सांस्कृतिक समरसता।",
        "category": "Culture",
        "difficulty": "intermediate",
    },

    # ═════════════════════════════════════════════════════════════════════════
    # 3. ADVANCED SENTENCES (~20 sentences)
    # ═════════════════════════════════════════════════════════════════════════
    {
        "text_hi": "दृढ़ संकल्प, आत्मसंयम और नियमित वाक्-अभ्यास से किसी भी उच्चारण दोष पर पूर्ण विजय प्राप्त की जा सकती है।",
        "transliteration": "Dridh sankalp, aatmasanyam aur niyamit vaak-abhyas se kisi bhi uchcharan dosh par poorna vijay prapt ki ja sakti hai.",
        "meaning_en": "With firm resolve, self-discipline, and disciplined speech exercises, any articulation disorder can be fully overcome.",
        "meaning_hi": "वाक्-चिकित्सा और निरंतर अभ्यास का वैज्ञानिक प्रभाव।",
        "category": "Speech Therapy",
        "difficulty": "advanced",
    },
    {
        "text_hi": "ध्वन्यात्मक शुद्धता और सटीक स्वर-तंत्रिका समन्वय से वाणी में अप्रतिम मधुरता और प्रभावशीलता उत्पन्न होती है।",
        "transliteration": "Dhvanyatmak shuddhata aur sateek swar-tantrika samanvay se vaani mein apratim madhurta aur prabhavsheelata utpann hoti hai.",
        "meaning_en": "Phonetic precision and accurate vocal-tract coordination produce unparalleled melody and efficacy in speech.",
        "meaning_hi": "उच्चारण-विज्ञान और स्वर-यंत्र का तालमेल।",
        "category": "Speech Therapy",
        "difficulty": "advanced",
    },
    {
        "text_hi": "मूर्धन्य और तालव्य व्यंजनों का स्पष्ट विभेदन करते समय जिह्वा की नोक को तालू के केंद्रीय भाग पर स्पर्श कराएं।",
        "transliteration": "Moordhanya aur talavya vyanjanon ka spasht vibhedan karte samay jihva ki nok ko talu ke kendreeya bhaag par sparsh karayein.",
        "meaning_en": "While clearly distinguishing between retroflex and palatal consonants, touch the tip of the tongue to the central hard palate.",
        "meaning_hi": "मूर्धन्य व तालव्य ध्वनियों का शुद्ध उच्चारण निर्देश।",
        "category": "Speech Therapy",
        "difficulty": "advanced",
    },
    {
        "text_hi": "प्राण-वायु के सुव्यवस्थित नियंत्रण और ओंठों के संकुचन-प्रसारण से कठिन संयुक्त अक्षरों का स्पष्ट उच्चारण संभव होता है।",
        "transliteration": "Praan-vaayu ke suvyavasthit niyantran aur onthon ke sankuchan-prasaaran se kathin sanyukt aksharon ka spasht uchcharan sambhav hota hai.",
        "meaning_en": "Through regulated breath airflow and coordinated labial contraction and expansion, clear articulation of complex conjuncts becomes possible.",
        "meaning_hi": "सांस और ओष्ठ संचालन से संयुक्त वर्णों का अभ्यास।",
        "category": "Speech Therapy",
        "difficulty": "advanced",
    },
    {
        "text_hi": "भारतीय दर्शन में 'वसुधैव कुटुम्बकम्' और 'सर्वे भवन्तु सुखिनः' की उदात्त चेतना युगों-युगों से प्रवाहित होती रही है।",
        "transliteration": "Bharatiya darshan mein 'Vasudhaiva Kutumbakam' aur 'Sarve Bhavantu Sukhinah' ki udaatta chetna yugon-yugon se pravahit hoti rahi hai.",
        "meaning_en": "In Indian philosophy, the noble ethos of universal brotherhood and collective happiness has flowed through the ages.",
        "meaning_hi": "वैश्विक बंधुत्व और मानवीय कल्याण का दार्शनिक उद्घोष।",
        "category": "Philosophy",
        "difficulty": "advanced",
    },
    {
        "text_hi": "महाकवि कालिदास विरचित 'अभिज्ञानशाकुन्तलम्' और 'मेघदूतम्' संस्कृत वाङ्मय की सर्वोत्कृष्ट कालजयी रचनाएं हैं।",
        "transliteration": "Mahakavi Kalidas virachit 'Abhigyanashakuntalam' aur 'Meghdootam' Sanskrit vaangmaya ki sarvotkrisht kaaljayi rachnayein hain.",
        "meaning_en": "The masterpieces 'Abhijnanashakuntalam' and 'Meghadutam' composed by the great poet Kalidasa are timeless pinnacles of Sanskrit literature.",
        "meaning_hi": "संस्कृत साहित्य और कालिदास की अमर कृतियां।",
        "category": "Literature",
        "difficulty": "advanced",
    },
    {
        "text_hi": "वैज्ञानिक अनुसंधान, तार्किक चिंतन और तकनीकी नवाचार ही किसी भी प्रगतिशील राष्ट्र के सर्वांगीण विकास का सशक्त आधार हैं।",
        "transliteration": "Vaigyanik anusandhan, tarkik chintan aur takneeki navachar hi kisi bhi pragatisheel rashtra ke sarvaangeen vikas ka sashakt aadhar hain.",
        "meaning_en": "Scientific research, logical reasoning, and technological innovation constitute the strong foundation for a nation's holistic progress.",
        "meaning_hi": "विज्ञान और नवाचार से राष्ट्र निर्माण।",
        "category": "Science & Tech",
        "difficulty": "advanced",
    },
    {
        "text_hi": "कृत्रिम बुद्धिमत्ता और तंत्रिका-संजाल प्रणालियों के विकास से मानवीय जीवन के प्रत्येक क्षेत्र में अभूतपूर्व परिवर्तन आ रहे हैं।",
        "transliteration": "Kritrim buddhimaata aur tantrika-sanjaal pranaliyon ke vikas se maanveey jeevan ke pratyek kshetra mein abhootpoorva parivartan aa rahe hain.",
        "meaning_en": "With the advancement of artificial intelligence and neural network architectures, unprecedented transformations are reshaping human society.",
        "meaning_hi": "एआई और न्यूरल नेटवर्क की आधुनिक क्रांति।",
        "category": "Technology",
        "difficulty": "advanced",
    },
    {
        "text_hi": "पर्यावरणीय संतुलन को अक्षुण्ण बनाए रखने हेतु नवीकरणीय ऊर्जा स्रोतों का अधिकाधिक दोहन अपरिहार्य हो चुका है।",
        "transliteration": "Paryavaraneeya santulan ko akshunna banaye rakhne hetu naveekaranaye urja sroton ka adhikaadhik dohan apariharya ho chuka hai.",
        "meaning_en": "To maintain ecological equilibrium intact, harnessing renewable energy resources to the maximum has become indispensable.",
        "meaning_hi": "हरित ऊर्जा और पारिस्थितिकीय संतुलन।",
        "category": "Environment",
        "difficulty": "advanced",
    },
    {
        "text_hi": "सहानुभूति, परोपकारिता और अंतःकरण की निर्मलता व्यक्ति को एक संवेदनशील, प्रबुद्ध और उत्तरदायी नागरिक बनाती है।",
        "transliteration": "Sahanubhuti, paropkarita aur antahkaran ki nirmalata vyakti ko ek samvedansheel, prabuddh aur uttardayi nagrik banati hai.",
        "meaning_en": "Empathy, altruism, and purity of conscience transform an individual into a sensitive, enlightened, and responsible citizen.",
        "meaning_hi": "चरित्र निर्माण और सामाजिक संवेदना।",
        "category": "Ethics",
        "difficulty": "advanced",
    },
]


def seed_sentences_sqlite():
    db_paths = [
        "backend/swarsaarthi.db",
        "swarsaarthi.db",
    ]
    
    for db_path in db_paths:
        if not os.path.exists(db_path):
            continue
        print(f"Seeding database at: {db_path}")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Check and add item_type column
        cols = [c[1] for c in cur.execute("PRAGMA table_info(words)").fetchall()]
        if "item_type" not in cols:
            print("Adding 'item_type' column...")
            cur.execute("ALTER TABLE words ADD COLUMN item_type VARCHAR(20) DEFAULT 'word'")
            conn.commit()

        # Ensure all existing words have item_type = 'word'
        cur.execute("UPDATE words SET item_type = 'word' WHERE item_type IS NULL")
        conn.commit()

        inserted = 0
        updated = 0
        for item in SENTENCES_DATA:
            cur.execute("SELECT id FROM words WHERE text_hi = ?", (item["text_hi"],))
            row = cur.fetchone()
            if row:
                cur.execute(
                    """
                    UPDATE words 
                    SET transliteration = ?, meaning_en = ?, meaning_hi = ?, 
                        difficulty = ?, category = ?, item_type = 'sentence'
                    WHERE id = ?
                    """,
                    (
                        item["transliteration"],
                        item["meaning_en"],
                        item["meaning_hi"],
                        item["difficulty"],
                        item["category"],
                        row[0],
                    ),
                )
                updated += 1
            else:
                cur.execute(
                    """
                    INSERT INTO words (id, text_hi, transliteration, meaning_en, meaning_hi, difficulty, category, item_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'sentence')
                    """,
                    (
                        str(uuid.uuid4()),
                        item["text_hi"],
                        item["transliteration"],
                        item["meaning_en"],
                        item["meaning_hi"],
                        item["difficulty"],
                        item["category"],
                    ),
                )
                inserted += 1

        conn.commit()
        
        # Verify counts
        word_count = cur.execute("SELECT COUNT(*) FROM words WHERE item_type = 'word'").fetchone()[0]
        sentence_count = cur.execute("SELECT COUNT(*) FROM words WHERE item_type = 'sentence'").fetchone()[0]
        print(f"Finished {db_path}: {inserted} inserted, {updated} updated.")
        print(f"Current DB totals -> Words: {word_count}, Sentences: {sentence_count}")
        conn.close()


if __name__ == "__main__":
    seed_sentences_sqlite()

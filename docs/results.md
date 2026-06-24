# RAG Evaluation Results

- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- LLM: `extractive fallback (no API key)`
- Chunks indexed: 28
- top-k: 4

## Summary metrics

- **Retrieval accuracy (expected section in top-4)**: 10/10 = 100%
- **Average top-1 cosine relevance**: 0.615
- **Average answer latency**: 0.01s

## Q: When and how was Rome founded according to tradition?
- Expected section keyword: `Origins` -> **HIT**
- Top-1 cosine score: `0.549`  | retrieval time: `3571 ms`
- Retrieved sections: [1. Origins and the Roman Republic], [8. Culture, Art, and Engineering], [6. Society and Daily Life], [12. Key Emperors and Dynasties]
- Answer latency: `0.01s`  (mode: extractive)

**Answer:**

(Extractive fallback — no LLM key set. Most relevant passages:)

[1. Origins and the Roman Republic] (score=0.549)
According to Roman tradition, the city of Rome was founded in 753 BCE on the banks of the river Tiber in central Italy. The legendary account credits the twin brothers Romulus and Remus, descendants of the Trojan hero Aeneas, with its founding, though modern archaeology shows that small Latin and Sabine villages on the seven hills had already merged into a single urban community by the eighth century BCE. Rome was first ruled by kings, traditionally seven of them, including Numa Pompilius, who is credited with establishing many religious institutions, and the Etruscan Tarquins. In 509 BCE the Romans expelled their last king, Tarquinius Superbus, and established the Republic (res publica, 'the public thing'). Political power was vested in elected magistrates, a powerful Senate, and popular assemblies. The two most senior magistrates were the consuls, elected annually in pairs so that each could veto the other, a deliberate safeguard against the return of monarchy. Below them stood praetors, who administered justice, aediles, who managed public works and games, and quaestors, who supervised finances. The early Republic was marked by the Conflict of the Orders, a long political struggle between the patricians (the hereditary aristocracy) and the plebeians (commoners). Over roughly two centuries the plebeians won the right to elect their own officials, the tribunes of the plebs, who could veto state actions, and eventually gained access to the highest offices.

[8. Culture, Art, and Engineering] (score=0.475)
Roman culture drew heavily on Greek models while developing a distinctive character of its own. In literature, the Augustan age produced some of Rome's greatest writers: Virgil, whose epic the Aeneid gave Rome a national myth; Horace and Ovid in poetry; and Livy in history. Later authors such as Tacitus, Seneca, and Pliny the Elder enriched history, philosophy, and natural science. Latin became the language of administration, law, and learning across the western empire and is the ancestor of the Romance languages. Roman art served public and political ends. Realistic portrait sculpture, triumphal arches, and monumental columns such as Trajan's Column celebrated rulers and commemorated victories. Wall paintings and intricate mosaics decorated homes and public buildings, and Roman copies preserved many lost works of Greek sculpture. Engineering was perhaps Rome's most visible legacy. Roman architects mastered the arch, the vault, and the dome, and pioneered the use of concrete (opus caementicium), which allowed structures of unprecedented scale. Aqueducts carried fresh water over great distances into cities; the Pont du Gard in southern France and the aqueduct of Segovia in Spain still stand today. The Colosseum could seat tens of thousands of spectators, and the Pantheon's vast unreinforced concrete dome remains an engineering marvel nearly two thousand years after its construction under Hadrian. The Romans also gave the world enduring practical innovations: the extensive paved road network summarised in the proverb 'all roads lead to Rome', sophisticated urban sanitation and sewers such as the Cloaca Maxima, public bathing complexes, central heating by hypocaust, and the Julian calendar introduced by Julius Caesar in 46 BCE, which, with later refinement, underlies the calendar used worldwide today.


---

## Q: How was the Roman legion organised and equipped?
- Expected section keyword: `Military` -> **HIT**
- Top-1 cosine score: `0.689`  | retrieval time: `9 ms`
- Retrieved sections: [4. The Roman Military], [7. Religion and Belief], [1. Origins and the Roman Republic], [6. Society and Daily Life]
- Answer latency: `0.01s`  (mode: extractive)

**Answer:**

(Extractive fallback — no LLM key set. Most relevant passages:)

[4. The Roman Military] (score=0.689)
The Roman army was the instrument of the empire's expansion and the guarantor of its frontiers. Its backbone was the legion, a formation of roughly 5,000 heavy infantry citizens, subdivided into ten cohorts and further into centuries commanded by centurions. Legionaries were equipped with the gladius (a short stabbing sword), the pilum (a heavy javelin), a large rectangular shield (scutum), and segmented armour. Discipline, engineering skill, and standardised tactics made the legion formidable. Alongside the legions served the auxilia, auxiliary units recruited from non-citizen provincials who provided cavalry, archers, and specialised troops. After completing around twenty-five years of service, auxiliaries were typically granted Roman citizenship, which they passed to their descendants, making the army a powerful engine of Romanisation. The army was also a vast engineering corps. Soldiers built roads, bridges, aqueducts, and fortified camps (castra) laid out to a standard plan. Many cities of Europe, including London, Cologne, and Vienna, grew from Roman military settlements. The famous frontier defences, such as Hadrian's Wall in northern Britain, marked the limits of direct imperial control. At its height the empire maintained roughly 28 to 30 legions plus auxiliaries, perhaps 300,000 to 400,000 men in total. The Praetorian Guard, an elite force stationed in and around Rome, served as the emperor's bodyguard but also became a dangerous political force, capable of making and unmaking emperors.

[7. Religion and Belief] (score=0.460)
Traditional Roman religion was polytheistic and deeply woven into public life. The Romans worshipped a pantheon of gods, many identified with Greek deities: Jupiter (Zeus), king of the gods; Juno (Hera); Neptune (Poseidon); Mars (Ares), the god of war especially honoured at Rome; Venus (Aphrodite); and Minerva (Athena). Public priesthoods, including the college of pontiffs and the Vestal Virgins who tended the sacred flame of the city, conducted rituals to maintain the pax deorum, the favourable disposition of the gods toward Rome. Religion and the state were inseparable. Augurs interpreted the will of the gods by observing the flight of birds and other signs, and no major public action was undertaken without consulting the auspices. From the time of Augustus, the imperial cult developed, in which deceased and sometimes living emperors were honoured as divine, providing a unifying focus of loyalty across the diverse empire. The empire was generally tolerant of the many local and foreign cults practised by its subjects, and eastern mystery religions such as the cults of Isis, Cybele, and Mithras attracted wide followings, the last especially popular among soldiers. Tolerance had limits, however: religions seen as politically subversive or as refusing the customary civic rites could be persecuted. Christianity emerged in the first century CE in the province of Judaea and spread through the empire's cities and trade networks.


---

## Q: What goods did Rome trade and with whom?
- Expected section keyword: `Economy` -> **HIT**
- Top-1 cosine score: `0.744`  | retrieval time: `9 ms`
- Retrieved sections: [5. Economy and Trade], [5. Economy and Trade], [13. Geography, Provinces, and Urban Life], [6. Society and Daily Life]
- Answer latency: `0.01s`  (mode: extractive)

**Answer:**

(Extractive fallback — no LLM key set. Most relevant passages:)

[5. Economy and Trade] (score=0.744)
The Roman economy was the largest and most integrated of the ancient Mediterranean world. Agriculture was its foundation: grain, olives, and grapes were the staple crops, and large estates called latifundia, often worked by slaves, produced surpluses for urban markets. Egypt and North Africa were the great granaries that fed the city of Rome, whose population may have reached one million people. A common currency, a network of roads spanning more than 80,000 kilometres, and the relative peace of the Pax Romana (roughly 27 BCE to 180 CE) enabled long-distance trade on an unprecedented scale. Standard coins such as the gold aureus, the silver denarius, and bronze sestertius circulated across the empire. Goods moved by sea wherever possible, since maritime transport was far cheaper than overland haulage. Trade extended well beyond imperial borders. Roman merchants imported silk from China along the Silk Road, spices and cotton from India, incense from Arabia, and amber from the Baltic. Excavations have found Roman coins in southern India and Roman glassware as far away as East Asia. In exchange Rome exported wine, olive oil, glassware, fine pottery (such as red-gloss terra sigillata), and manufactured goods. The state managed key sectors directly. The annona, the grain supply, was a major administrative concern, and free or subsidised grain distributions to the urban poor were a tool of political stability.

[5. Economy and Trade] (score=0.635)
spices and cotton from India, incense from Arabia, and amber from the Baltic. Excavations have found Roman coins in southern India and Roman glassware as far away as East Asia. In exchange Rome exported wine, olive oil, glassware, fine pottery (such as red-gloss terra sigillata), and manufactured goods. The state managed key sectors directly. The annona, the grain supply, was a major administrative concern, and free or subsidised grain distributions to the urban poor were a tool of political stability. Mines in Spain and elsewhere, often worked by slaves and convicts, supplied the precious metals that underpinned the coinage. In the third century CE, repeated debasement of the silver coinage contributed to severe inflation and economic disruption.


---

## Q: What was the role of slaves in Roman society?
- Expected section keyword: `Society` -> **HIT**
- Top-1 cosine score: `0.640`  | retrieval time: `9 ms`
- Retrieved sections: [6. Society and Daily Life], [14. Women, Family, and Education], [6. Society and Daily Life], [14. Women, Family, and Education]
- Answer latency: `0.01s`  (mode: extractive)

**Answer:**

(Extractive fallback — no LLM key set. Most relevant passages:)

[6. Society and Daily Life] (score=0.640)
Roman society was strongly hierarchical and built around the household. At its head stood the paterfamilias, the senior male, who held extensive legal authority (patria potestas) over his wife, children, and slaves. Social status was defined by a combination of birth, wealth, and citizenship. The senatorial and equestrian orders formed the elite, below whom stood ordinary citizens, freedmen (manumitted former slaves), and slaves. Slavery was pervasive and economically fundamental. Slaves worked in households, farms, mines, workshops, and even as physicians, teachers, and administrators. Many were prisoners of war; others were born into slavery. Manumission was relatively common, and freed slaves could become citizens, though they carried certain legal disabilities. Their freeborn children, however, enjoyed full citizenship, allowing remarkable social mobility over generations. Citizenship was the key legal status of the Roman world, conferring rights such as the ability to make contracts, marry legally, vote, and appeal to the emperor. Over time citizenship spread from Rome to Italy and then to the provinces. In 212 CE the emperor Caracalla issued the Antonine Constitution (Constitutio Antoniniana), granting Roman citizenship to almost all free inhabitants of the empire. Daily life varied enormously by class. The wealthy lived in spacious town houses (domus) and country villas with mosaics, frescoes, and running water, while the urban poor crowded into multi-storey apartment blocks called insulae, which were often cramped and prone to fire.

[14. Women, Family, and Education] (score=0.559)
The Roman family was the basic unit of society, and the ideal of family loyalty (pietas) was central to Roman values. Marriage was primarily a social and economic institution, often arranged to cement alliances between families. While the paterfamilias held formal legal authority, in practice many Roman women, especially among the elite, exercised considerable influence over household affairs, property, and even politics behind the scenes. The legal and social position of women evolved over time. Although women could not vote or hold public office, Roman women could own and inherit property, run businesses, and initiate divorce, rights that were unusual in the ancient world. Influential women such as Livia, the wife of Augustus, and Agrippina the Younger, mother of Nero, wielded real power at the heart of the imperial court, even if they did so through male relatives. Education reflected social class. Wealthy children, both boys and girls, were taught at home by tutors or attended schools where they learned reading, writing, and arithmetic, followed for boys by training in rhetoric and Greek literature considered essential for a public career. The poor received little or no formal schooling. Literacy, while far from universal, was widespread enough that inscriptions, graffiti, and notices were a normal part of urban life. Childhood in Rome was precarious, with high infant mortality, and children were expected to take on adult responsibilities relatively early.


---

## Q: How did Christianity become the official religion of Rome?
- Expected section keyword: `Religion` -> **HIT**
- Top-1 cosine score: `0.638`  | retrieval time: `10 ms`
- Retrieved sections: [7. Religion and Belief], [7. Religion and Belief], [9. Crisis, Reform, and Division], [10. Decline and Fall of the West]
- Answer latency: `0.01s`  (mode: extractive)

**Answer:**

(Extractive fallback — no LLM key set. Most relevant passages:)

[7. Religion and Belief] (score=0.638)
diverse empire. The empire was generally tolerant of the many local and foreign cults practised by its subjects, and eastern mystery religions such as the cults of Isis, Cybele, and Mithras attracted wide followings, the last especially popular among soldiers. Tolerance had limits, however: religions seen as politically subversive or as refusing the customary civic rites could be persecuted. Christianity emerged in the first century CE in the province of Judaea and spread through the empire's cities and trade networks. Early Christians faced periodic persecution because they refused to participate in the imperial cult and traditional sacrifices. The situation changed dramatically when the emperor Constantine issued the Edict of Milan in 313 CE, granting religious toleration. Christianity grew rapidly thereafter, and in 380 CE the emperor Theodosius I made Nicene Christianity the official religion of the empire.

[7. Religion and Belief] (score=0.538)
Traditional Roman religion was polytheistic and deeply woven into public life. The Romans worshipped a pantheon of gods, many identified with Greek deities: Jupiter (Zeus), king of the gods; Juno (Hera); Neptune (Poseidon); Mars (Ares), the god of war especially honoured at Rome; Venus (Aphrodite); and Minerva (Athena). Public priesthoods, including the college of pontiffs and the Vestal Virgins who tended the sacred flame of the city, conducted rituals to maintain the pax deorum, the favourable disposition of the gods toward Rome. Religion and the state were inseparable. Augurs interpreted the will of the gods by observing the flight of birds and other signs, and no major public action was undertaken without consulting the auspices. From the time of Augustus, the imperial cult developed, in which deceased and sometimes living emperors were honoured as divine, providing a unifying focus of loyalty across the diverse empire. The empire was generally tolerant of the many local and foreign cults practised by its subjects, and eastern mystery religions such as the cults of Isis, Cybele, and Mithras attracted wide followings, the last especially popular among soldiers. Tolerance had limits, however: religions seen as politically subversive or as refusing the customary civic rites could be persecuted. Christianity emerged in the first century CE in the province of Judaea and spread through the empire's cities and trade networks.


---

## Q: What engineering innovations are the Romans known for?
- Expected section keyword: `Engineering` -> **HIT**
- Top-1 cosine score: `0.542`  | retrieval time: `9 ms`
- Retrieved sections: [8. Culture, Art, and Engineering], [8. Culture, Art, and Engineering], [5. Economy and Trade], [4. The Roman Military]
- Answer latency: `0.01s`  (mode: extractive)

**Answer:**

(Extractive fallback — no LLM key set. Most relevant passages:)

[8. Culture, Art, and Engineering] (score=0.542)
Roman culture drew heavily on Greek models while developing a distinctive character of its own. In literature, the Augustan age produced some of Rome's greatest writers: Virgil, whose epic the Aeneid gave Rome a national myth; Horace and Ovid in poetry; and Livy in history. Later authors such as Tacitus, Seneca, and Pliny the Elder enriched history, philosophy, and natural science. Latin became the language of administration, law, and learning across the western empire and is the ancestor of the Romance languages. Roman art served public and political ends. Realistic portrait sculpture, triumphal arches, and monumental columns such as Trajan's Column celebrated rulers and commemorated victories. Wall paintings and intricate mosaics decorated homes and public buildings, and Roman copies preserved many lost works of Greek sculpture. Engineering was perhaps Rome's most visible legacy. Roman architects mastered the arch, the vault, and the dome, and pioneered the use of concrete (opus caementicium), which allowed structures of unprecedented scale. Aqueducts carried fresh water over great distances into cities; the Pont du Gard in southern France and the aqueduct of Segovia in Spain still stand today. The Colosseum could seat tens of thousands of spectators, and the Pantheon's vast unreinforced concrete dome remains an engineering marvel nearly two thousand years after its construction under Hadrian. The Romans also gave the world enduring practical innovations: the extensive paved road network summarised in the proverb 'all roads lead to Rome', sophisticated urban sanitation and sewers such as the Cloaca Maxima, public bathing complexes, central heating by hypocaust, and the Julian calendar introduced by Julius Caesar in 46 BCE, which, with later refinement, underlies the calendar used worldwide today.

[8. Culture, Art, and Engineering] (score=0.488)
the Pantheon's vast unreinforced concrete dome remains an engineering marvel nearly two thousand years after its construction under Hadrian. The Romans also gave the world enduring practical innovations: the extensive paved road network summarised in the proverb 'all roads lead to Rome', sophisticated urban sanitation and sewers such as the Cloaca Maxima, public bathing complexes, central heating by hypocaust, and the Julian calendar introduced by Julius Caesar in 46 BCE, which, with later refinement, underlies the calendar used worldwide today.


---

## Q: Why did the Western Roman Empire fall in 476 CE?
- Expected section keyword: `Decline` -> **HIT**
- Top-1 cosine score: `0.723`  | retrieval time: `14 ms`
- Retrieved sections: [10. Decline and Fall of the West], [10. Decline and Fall of the West], [12. Key Emperors and Dynasties], [12. Key Emperors and Dynasties]
- Answer latency: `0.01s`  (mode: extractive)

**Answer:**

(Extractive fallback — no LLM key set. Most relevant passages:)

[10. Decline and Fall of the West] (score=0.723)
new peoples all weakened the western state. By convention, the Western Roman Empire is said to have fallen in 476 CE, when the Germanic commander Odoacer deposed the last western emperor, the young Romulus Augustulus, and ruled Italy as a king rather than restoring an emperor. Historians today emphasise that this was less a sudden collapse than a long transformation, in which Roman institutions, law, language, and the Christian Church persisted and blended with those of the new Germanic kingdoms. The Eastern Roman Empire, known to later historians as the Byzantine Empire, survived for nearly another thousand years. It preserved Roman law, Greek learning, and Christian culture, reaching a high point under Justinian I in the sixth century, before finally falling to the Ottoman Turks with the capture of Constantinople in 1453 CE.

[10. Decline and Fall of the West] (score=0.662)
The Western Roman Empire faced mounting pressures in the late fourth and fifth centuries CE. Migrating and invading peoples, including the Goths, Vandals, Franks, and Huns, pressed across the frontiers, sometimes settling within imperial territory as federated allies and sometimes plundering its provinces. The disastrous Roman defeat at the Battle of Adrianople in 378 CE, in which the emperor Valens was killed by the Goths, exposed the military weakness of the late Roman state. Rome itself, no longer the administrative capital, was sacked twice in the fifth century: by the Visigoths under Alaric in 410 CE and by the Vandals in 455 CE. These events sent a profound psychological shock through the Roman world, even though the city had ceased to be the centre of government. Internal problems compounded external threats: political instability, the cost of defence, heavy taxation, and the difficulty of integrating new peoples all weakened the western state. By convention, the Western Roman Empire is said to have fallen in 476 CE, when the Germanic commander Odoacer deposed the last western emperor, the young Romulus Augustulus, and ruled Italy as a king rather than restoring an emperor. Historians today emphasise that this was less a sudden collapse than a long transformation, in which Roman institutions, law, language, and the Christian Church persisted and blended with those of the new Germanic kingdoms.


---

## Q: Who were the Five Good Emperors?
- Expected section keyword: `Emperors` -> **HIT**
- Top-1 cosine score: `0.559`  | retrieval time: `10 ms`
- Retrieved sections: [12. Key Emperors and Dynasties], [12. Key Emperors and Dynasties], [3. Imperial Government and Administration], [6. Society and Daily Life]
- Answer latency: `0.01s`  (mode: extractive)

**Answer:**

(Extractive fallback — no LLM key set. Most relevant passages:)

[12. Key Emperors and Dynasties] (score=0.559)
and second centuries CE are often regarded as the empire's golden age, the era of the so-called Five Good Emperors: Nerva, Trajan, Hadrian, Antoninus Pius, and Marcus Aurelius. Under Trajan (reigned 98-117 CE) the empire reached its greatest territorial extent, stretching from Britain to Mesopotamia. Hadrian consolidated the frontiers and built the wall in Britain that bears his name, while Marcus Aurelius, a Stoic philosopher, wrote his Meditations even as he campaigned on the Danube. Later dynasties faced harder times. The Severan dynasty (193-235 CE) leaned heavily on the army, and Septimius Severus reputedly advised his sons to enrich the soldiers and despise everyone else. After the third-century crisis, Diocletian and Constantine reshaped the empire entirely, and the Constantinian and Theodosian dynasties presided over the empire's Christianisation and eventual division between East and West.

[12. Key Emperors and Dynasties] (score=0.543)
Augustus (reigned 27 BCE - 14 CE), the first emperor, founded the Julio-Claudian dynasty and presided over a long period of internal peace and consolidation. He reformed the army, the tax system, and the administration of Rome, boasting that he had found the city built of brick and left it clad in marble. His long reign set the template for the imperial office that his successors inherited. The Julio-Claudians who followed were a mixed group. Tiberius was an able but suspicious administrator; Caligula and Nero became bywords for cruelty and extravagance, the latter blamed (probably unfairly) for the Great Fire of Rome in 64 CE. The dynasty ended with Nero's suicide in 68 CE, triggering the chaotic Year of the Four Emperors in 69 CE, from which Vespasian emerged to found the Flavian dynasty and begin construction of the Colosseum. The late first and second centuries CE are often regarded as the empire's golden age, the era of the so-called Five Good Emperors: Nerva, Trajan, Hadrian, Antoninus Pius, and Marcus Aurelius. Under Trajan (reigned 98-117 CE) the empire reached its greatest territorial extent, stretching from Britain to Mesopotamia. Hadrian consolidated the frontiers and built the wall in Britain that bears his name, while Marcus Aurelius, a Stoic philosopher, wrote his Meditations even as he campaigned on the Danube. Later dynasties faced harder times.


---

## Q: What rights did Roman women have?
- Expected section keyword: `Women` -> **HIT**
- Top-1 cosine score: `0.653`  | retrieval time: `11 ms`
- Retrieved sections: [14. Women, Family, and Education], [6. Society and Daily Life], [6. Society and Daily Life], [1. Origins and the Roman Republic]
- Answer latency: `0.01s`  (mode: extractive)

**Answer:**

(Extractive fallback — no LLM key set. Most relevant passages:)

[14. Women, Family, and Education] (score=0.653)
The Roman family was the basic unit of society, and the ideal of family loyalty (pietas) was central to Roman values. Marriage was primarily a social and economic institution, often arranged to cement alliances between families. While the paterfamilias held formal legal authority, in practice many Roman women, especially among the elite, exercised considerable influence over household affairs, property, and even politics behind the scenes. The legal and social position of women evolved over time. Although women could not vote or hold public office, Roman women could own and inherit property, run businesses, and initiate divorce, rights that were unusual in the ancient world. Influential women such as Livia, the wife of Augustus, and Agrippina the Younger, mother of Nero, wielded real power at the heart of the imperial court, even if they did so through male relatives. Education reflected social class. Wealthy children, both boys and girls, were taught at home by tutors or attended schools where they learned reading, writing, and arithmetic, followed for boys by training in rhetoric and Greek literature considered essential for a public career. The poor received little or no formal schooling. Literacy, while far from universal, was widespread enough that inscriptions, graffiti, and notices were a normal part of urban life. Childhood in Rome was precarious, with high infant mortality, and children were expected to take on adult responsibilities relatively early.

[6. Society and Daily Life] (score=0.591)
Roman society was strongly hierarchical and built around the household. At its head stood the paterfamilias, the senior male, who held extensive legal authority (patria potestas) over his wife, children, and slaves. Social status was defined by a combination of birth, wealth, and citizenship. The senatorial and equestrian orders formed the elite, below whom stood ordinary citizens, freedmen (manumitted former slaves), and slaves. Slavery was pervasive and economically fundamental. Slaves worked in households, farms, mines, workshops, and even as physicians, teachers, and administrators. Many were prisoners of war; others were born into slavery. Manumission was relatively common, and freed slaves could become citizens, though they carried certain legal disabilities. Their freeborn children, however, enjoyed full citizenship, allowing remarkable social mobility over generations. Citizenship was the key legal status of the Roman world, conferring rights such as the ability to make contracts, marry legally, vote, and appeal to the emperor. Over time citizenship spread from Rome to Italy and then to the provinces. In 212 CE the emperor Caracalla issued the Antonine Constitution (Constitutio Antoniniana), granting Roman citizenship to almost all free inhabitants of the empire. Daily life varied enormously by class. The wealthy lived in spacious town houses (domus) and country villas with mosaics, frescoes, and running water, while the urban poor crowded into multi-storey apartment blocks called insulae, which were often cramped and prone to fire.


---

## Q: What was the Crisis of the Third Century?
- Expected section keyword: `Crisis` -> **HIT**
- Top-1 cosine score: `0.411`  | retrieval time: `11 ms`
- Retrieved sections: [9. Crisis, Reform, and Division], [12. Key Emperors and Dynasties], [11. Legacy of Rome], [10. Decline and Fall of the West]
- Answer latency: `0.01s`  (mode: extractive)

**Answer:**

(Extractive fallback — no LLM key set. Most relevant passages:)

[9. Crisis, Reform, and Division] (score=0.411)
The relative stability of the Pax Romana gave way in the third century CE to a prolonged period of upheaval known as the Crisis of the Third Century (235-284 CE). The empire was beset by a rapid succession of short-lived 'barracks emperors' raised and deposed by the army, civil wars, devastating plagues, economic collapse, and simultaneous invasions along the Rhine, Danube, and eastern frontiers. At one point the empire fragmented into three competing states before being reunited. Stability was restored by the emperor Diocletian (reigned 284-305 CE), who undertook sweeping reforms. He reorganised provincial administration, expanded the bureaucracy and army, attempted to curb inflation with a price edict, and established the Tetrarchy, a system in which the empire was governed by two senior emperors (Augusti) and two junior colleagues (Caesares) to share the immense burden of defence and administration. Constantine the Great (reigned 306-337 CE) reunified the empire under a single ruler, embraced Christianity, and in 330 CE founded a new eastern capital at Byzantium, which he renamed Constantinople (modern Istanbul). Strategically located on the straits between Europe and Asia, the new capital reflected the growing economic and demographic weight of the eastern provinces. After the death of Theodosius I in 395 CE, the empire was permanently divided for administrative purposes between his two sons, creating a Western Roman Empire centred on Italy and an Eastern Roman Empire centred on Constantinople.

[12. Key Emperors and Dynasties] (score=0.325)
and second centuries CE are often regarded as the empire's golden age, the era of the so-called Five Good Emperors: Nerva, Trajan, Hadrian, Antoninus Pius, and Marcus Aurelius. Under Trajan (reigned 98-117 CE) the empire reached its greatest territorial extent, stretching from Britain to Mesopotamia. Hadrian consolidated the frontiers and built the wall in Britain that bears his name, while Marcus Aurelius, a Stoic philosopher, wrote his Meditations even as he campaigned on the Danube. Later dynasties faced harder times. The Severan dynasty (193-235 CE) leaned heavily on the army, and Septimius Severus reputedly advised his sons to enrich the soldiers and despise everyone else. After the third-century crisis, Diocletian and Constantine reshaped the empire entirely, and the Constantinian and Theodosian dynasties presided over the empire's Christianisation and eventual division between East and West.


---

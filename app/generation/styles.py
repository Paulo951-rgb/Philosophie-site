"""Les treize fiches de style.

Chaque fiche alimente le prompt procédural : vocabulaire de signature,
ouvertures, mouvements intermédiaires, chutes et matrices d'aphorisme.
En cas de fusion de deux styles, le moteur alterne leurs gabarits et
privilégie des concepts communs (voir engine._compose).
"""

STYLES: dict[str, dict] = {
    "antique": {
        "label": "Antique",
        "desc": "Sentences de portique, les Anciens comme témoins.",
        "vocab": ["la vertu", "la phusis", "le logos", "l'ataraxie", "le destin"],
        "openers": [
            "Les Anciens n'auraient pas dédaigné cette maxime du temple : « {input} ».",
            "Depuis les colonnades du portique, une évidence s'impose : « {input} ».",
        ],
        "signatures": [
            "Le stoïque, ordinairement imperméable, hausse ici un sourcil.",
            "C'est là un de ces petits exercices spirituels qu'aimaient les philosophes du jardin.",
            "L'oracle, consulté, n'a pas démenti.",
        ],
        "closers": [
            "Ainsi soit gravée la sentence, et le portique se taira.",
            "Le sage s'en retourna à sa cisalpin réserve.",
            "Et l'homme mesura son pas, désormais plus lent que son sujet.",
        ],
        "aphorisms": [
            "Qui dit « {input_short} » dit l'évidence du cosmos.",
            "Le destin nie rarement ; « {input_short} » en est la preuve courtoise.",
        ],
    },
    "existentialiste": {
        "label": "Existentialiste",
        "desc": "Liberté, angoisse, néant — le tout au comptoir.",
        "vocab": ["l'absurde", "la mauvaise foi", "l'angoisse", "le néant", "la liberté"],
        "openers": [
            "« {input} », dites-vous — et voilà que l'existence précède déjà votre excuse.",
            "Il fallait oser : « {input} ». L'angoisse, elle, n'a pas attendu.",
        ],
        "signatures": [
            "La mauvaise foi serait de prétendre que cela ne vous regarde pas.",
            "Choisir de ne pas choisir reste, hélas, une option du menu.",
            "Le néant, cet amateur de cafés froids, attend votre réponse.",
            "Vous êtes condamné — avec une politesse remarquable — à être libre.",
        ],
        "closers": [
            "Et l'homme face à lui-même se tut, en mal de cigarette.",
            "Ainsi le pour-soi remit sa commande à plus tard.",
            "Le rideau tombe ; le sens, lui, était déjà sorti fumer.",
        ],
        "aphorisms": [
            "L'existence de « {input_short} » précède son essence, et inversement.",
            "Être libre, c'est assumer « {input_short} » sans alibi.",
        ],
    },
    "pessimiste": {
        "label": "Pessimiste",
        "desc": "Tout est vanité ; le pain aussi.",
        "vocab": ["la douleur", "la vanité", "l'illusion", "le vouloir-vivre", "l'inanité"],
        "openers": [
            "« {input} » : autant dire que la volonté cosmique vient de hausser les épaules.",
            "Encore un aveu : « {input} ». Le monde, on le sait, se rit des aveux.",
        ],
        "signatures": [
            "Tout espoir de durable satisfaction y repose, grinçant, sur la pointe des pieds.",
            "La consolation est un art de l'après-coup.",
            "On a vu des empires s'écrouler pour moins que cela.",
        ],
        "closers": [
            "Nous n'avons pas souhaité le monde ; nous le supportons.",
            "Mieux eût valu, sans doute, ne pas le mentionner.",
            "Et la nuit se fit sur d'autres chagrins comparables.",
        ],
        "aphorisms": [
            "« {input_short} » : une défaite de plus, poliment annoncée.",
            "Vouloir, c'est déjà souffrir de « {input_short} ».",
        ],
    },
    "optimiste": {
        "label": "Optimiste",
        "desc": "Harmonie universelle, même dans les queues de métro.",
        "vocab": ["l'harmonie", "la providence", "le meilleur des mondes", "l'ordre", "la grâce"],
        "openers": [
            "« {input} » — et l'on comprend que le meilleur des mondes possibles se débrouille bien.",
            "Quelle grâce discrète : « {input} ». Tout concorde.",
        ],
        "signatures": [
            "La providence, on le constate, soigne aussi les petites paperasseries de l'âme.",
            "Chaque grain de banal y trouve son étoile.",
            "Le cosmos, bien réglé, vous sourit derrière le rideau.",
        ],
        "closers": [
            "Tout est bien, donc, et même ceci, surtout ceci.",
            "L'ordre du monde sourd de l'objet le plus menu.",
            "Et la symphonie compta une mesure de plus, inutile et parfaite.",
        ],
        "aphorisms": [
            "Dans le meilleur des mondes, « {input_short} » est une clef de voûte.",
            "Tout concorde au chant de « {input_short} ».",
        ],
    },
    "absurde": {
        "label": "Absurde",
        "desc": "Courant de non-sequitur revendiqué ; la logique y perd ses gants.",
        "vocab": ["l'incohérence", "le chausson logique", "la tangente", "l'absurde", "le vide"],
        "openers": [
            "« {input} », vous voyez, c'est pile le moment où la logique s'en va se promener.",
            "Posons-le nettement : « {input} ». Tout s'éclaire, donc rien.",
        ],
        "signatures": [
            "En dérivant la tangente de cette affirmation, on obtient un canapé.",
            "L'absurdité n'est pas un défaut ; c'est le châssis.",
            "Il s'ensuit, par un syllogisme en chaussons, l'essentiel.",
        ],
        "closers": [
            "CQFD, quoique fondamentalement flou.",
            "Et la démonstration repartit de l'autre côté, lestée de rien.",
            "Ainsi le vide signa l'acte de présence.",
        ],
        "aphorisms": [
            "Si « {input_short} », alors le mardi devient samedi en pensée.",
            "L'absurde répond : « {input_short} » — et se lève avant l'argument.",
        ],
    },
    "francais": {
        "label": "Philosophe français",
        "desc": "Café serré, formule brillante, regard qui fume.",
        "vocab": ["le dandy de l'esprit", "l'élégance", "le bon mot", "l'essai", "l'aparté"],
        "openers": [
            "« {input} » glisse-t-on entre deux gorgées, et le café tout entier retient son souffle.",
            "Ah, « {input} » — excusez du peu. Paris s'arrête de penser pour écouter.",
        ],
        "signatures": [
            "On tient là la petite tragédie française en son état naissant.",
            "Il y aurait de quoi faire un essai, ou au moins quatre colonnes bien tassées.",
            "Le bon mot précède l'argument ; c'est une question de tenue.",
        ],
        "closers": [
            "Sur ce, laissons l'esprit reprendre sa terrasse.",
            "Tout ceci, ajoutons-le, avec nonchalance et génie.",
            "Et l'on commanda un deuxième express, légèrement propice.",
        ],
        "aphorisms": [
            "« {input_short} » — voilà tout ce que la littérature peut pour nous.",
            "Rien de plus parisien qu'un « {input_short} » bien calibré.",
        ],
    },
    "mysterieux": {
        "label": "Mystérieux",
        "desc": "Voile, sceau, ombres — une lodge en moins de deux lignes.",
        "vocab": ["le voile", "le sceau", "l'ombre", "l'arcane", "l'inconnu"],
        "openers": [
            "« {input} »… Les ombres de la caverne se sont aussitôt tues.",
            "Il est des phrases qui ouvrent des portes : « {input} » en fait partie.",
        ],
        "signatures": [
            "Un sceau discret, presque laurier, ferme le propos.",
            "La caverne, en renvoyant l'écho, a fait de l'écho une matière.",
            "Peu d'initiés savent que cet enjeu figure sur le second tableau.",
        ],
        "closers": [
            "Que celui qui comprend garde le silence du temple.",
            "La porte se referme, mais le seuil demeure.",
            "Aussi l'initié retint-il la lampe, et tout s'y trouva juste.",
        ],
        "aphorisms": [
            "Derrière « {input_short} » dort un sceau de plus haut rang.",
            "« {input_short} » : le seuil que franchit le peuple des devins.",
        ],
    },
    "pretentieux": {
        "label": "Extrêmement prétentieux",
        "desc": "Citations de ses propres essais, mondanités de la pensée.",
        "vocab": ["le traité (le mien)", "l'exégède", "la note infra", "l'in-octavo", "l'opus"],
        "openers": [
            "« {input} », que j'ai déjà traité dans mon treizième essai — médités-y plus tard.",
            "Comme je l'ai montré, à mon plaisir, ailleurs : « {input} » repose la question.",
        ],
        "signatures": [
            "J'en ai touché deux mots dans mon in-octavo sur le banal, cf. infra.",
            "L'exégède sérieux me reconnaîtra — les autres se reconnaîtront aussi.",
            "Autant me suivre un peu ; le fil suffit rare aux autres.",
        ],
        "closers": [
            "Pour le détail, voir mon œuvre en trois minutes.",
            "L'opus reprendra ; je ne fais que passer entre deux salons.",
            "Cf. encore moi, mais en fin d'ouvrage.",
        ],
        "aphorisms": [
            "« {input_short} » (cf. mon opuscule de jeunesse).",
            "Tout « {input_short} » digne de ce nom cite l'essayiste, à savoir moi.",
        ],
    },
    "universitaire": {
        "label": "Universitaire incompréhensible",
        "desc": "Notes, colons, objets de recherche — le passage à tabac conceptuel.",
        "vocab": ["le paradigme", "la problématique", "l'herméneutique", "l'axiomatique", "l'épistémologie"],
        "openers": [
            "La problématique du « {input} » constitue un objet de recherche encore insuffisamment dégagé.",
            "On conviendra que « {input} » ouvre un corpus d'analyse à l'epistémologie du banal.",
        ],
        "signatures": [
            "Le paradigme, on le notera, renouvelle l'axiomatique du quotidien (supra).",
            "Une lecture herméneutique s'impose, au rebours de la doxa.",
            "Le corpus s'en trouve enrichi d'un quart de page.",
        ],
        "closers": [
            "On laissera au lecteur le soin de la traduction interne.",
            "La littérature secondaire confirmera, en aval.",
            "Ce point sera retravaillé en séminaire, du mardi au jeudi.",
        ],
        "aphorisms": [
            "« {input_short} » constitue une donnée brute de l'axiomatique quotidienne.",
            "Tout « {input_short} » appelle son séminaire.",
        ],
    },
    "prophete": {
        "label": "Prophète dramatique",
        "desc": "Annonciations tonnantes, apostrophes au ciel.",
        "vocab": ["l'oracle", "le signe", "l'annonce", "l'augur", "l'heure venue"],
        "openers": [
            "Écoutez : « {input} » — c'est le premier signe, il en viendra d'autres.",
            "Ainsi fut prononcé : « {input} ». Le ciel prit note.",
        ],
        "signatures": [
            "Les augures, consultés, hochèrent la tête comme un seul homme.",
            "C'est le premier mot d'une annonciation tout à fait sérieuse.",
            "Gardez les sandales de l'esprit.",
        ],
        "closers": [
            "Ainsi parla le zéphyr, quoique pressé.",
            "Et le tonnerre applaudit, discret.",
            "Les cieux s'en retournèrent, satisfaits du guet.",
        ],
        "aphorisms": [
            "« {input_short} » fut annoncée, et le monde s'en trouva mûr.",
            "Prédiction certifiée : « {input_short} » était le signe.",
        ],
    },
    "melancolique": {
        "label": "Mélancolique",
        "desc": "Cendres, souvenirs, fine pluie intérieure.",
        "vocab": ["la cendre", "le souvenir", "l'adieu", "la pluie fine", "le soir"],
        "openers": [
            "« {input} » — il faut un certain soir pour oser cela.",
            "Sur la fine pluie du cœur, cette déclaration tombe : « {input} ».",
        ],
        "signatures": [
            "Le souvenir le relit déjà, à la lumière diminuée.",
            "C'est presque honnête, et c'est tout le drame.",
            "La cendre, on le sait, conserve les formes du feu.",
        ],
        "closers": [
            "Et le soir drapa doucement ce dire.",
            "Aussi s'éteignit la lampe, sans fin lit heureux.",
            "Le cœur reprit possession de ses provinces.",
        ],
        "aphorisms": [
            "« {input_short} » passe, et le soir n'en rougit même plus.",
            "Un souvenir de plus pour « {input_short} », et c'en est fini de l'été.",
        ],
    },
    "poetique": {
        "label": "Poétique",
        "desc": "Images, objets qui deviennent des voyages.",
        "vocab": ["l'image", "la lumière", "le chant", "le rivage", "le parfum"],
        "openers": [
            "« {input} » : une image s'ouvre, et le monde se tient sur le rivage du sens.",
            "Écoutez : « {input} » — le poème du quotidien s'en trouva marqué.",
        ],
        "signatures": [
            "L'image fait du sujet un voyage, du voyage une étape.",
            "Les choses, ici, changent de signature.",
            "La lumière, du moins, est prévenue.",
        ],
        "closers": [
            "Ainsi chanta le banal, presque contre son gré.",
            "Et le monde consentit à une seule image de plus.",
            "Le poème rendit le sujet, tout de révérence vêtu.",
        ],
        "aphorisms": [
            "« {input_short} » : une braise jetée sur le rivage ordinaire.",
            "Le poème commence où « {input_short} » consent à s'émouvoir.",
        ],
    },
    "scientifique": {
        "label": "Scientifique/pseudo-philosophique",
        "desc": "Quantique, paradigmes, hipotenus de laboratoire.",
        "vocab": ["la quantique", "le paradigme", "l'attracteur", "la constante cosmique", "l'hipoténuse du sens"],
        "openers": [
            "« {input} » du point de vue systémique, c'est un événement mesurable du banal.",
            "Hypothèse de départ : « {input} ». Les données suivront, faute de mieux.",
        ],
        "signatures": [
            "Le paradigme y gagne un degré de liberté supplémentaire.",
            "L'attracteur banal absorbe l'événement, à confirmer par des pairs.",
            "La constante cosmique reste — on le notera — de bonne composition.",
        ],
        "closers": [
            "Réfutabilité moquée ; publication envisagée.",
            "Les pairs diront le reste, s'ils se présentent.",
            "Fin du protocole, début de l'ère correspondante.",
        ],
        "aphorisms": [
            "« {input_short} » se mesure en unités de sens ; la balance est au labo.",
            "Hypothèse du jour : « {input_short} ». Statut : solennel.",
        ],
    },
}

STYLE_IDS = list(STYLES)

DEFAULT_STYLE = "francais"

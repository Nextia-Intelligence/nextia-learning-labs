"""What the IVR says. Short sentences, the options last, numbers read in groups."""

WELCOME = ("Welcome to Larkfield. You are talking to an automated assistant. For English, say English or press 1. "
           "Pour le français, dites français ou appuyez sur 2.")

P = {
    "en": {
        "menu": "How can I help? Say order status, opening hours, or start a return. You can also press 1 for orders, "
                "2 for opening hours, 3 for returns, or 0 for a person.",
        "menu_retry": "Sorry, I did not get that. Please use your keypad: press 1 for orders, 2 for opening hours, "
                      "3 for returns, or 0 for a person.",
        "number": "Please say or type your six-digit order number.",
        "number_retry": "That number does not look right. Please type it on your keypad, one digit at a time.",
        "number_rest": "I heard {digits}. Please say the rest of the number.",
        "not_found": "I cannot find that order. Please type the number on your keypad.",
        "confirm": "Order {digits}. Is that right? Say yes or no, or press 1 for yes and 2 for no.",
        "confirm_retry": "Please say yes or no, or press 1 for yes and 2 for no.",
        "language_retry": "Sorry. Press 1 for English. Appuyez sur 2 pour le français.",
        "hours": "We are open Monday to Friday from 8 a.m. to 8 p.m., and Saturday from 9 a.m. to 5 p.m., Eastern "
                 "time. Thank you for calling Larkfield. Goodbye.",
        "status": {
            "processing": "Your {product} is being prepared and should ship by {date}.",
            "shipped": "Your {product} shipped on {date} and is on its way.",
            "out_for_delivery": "Your {product} is out for delivery today.",
            "delivered": "Your {product} was delivered on {date}.",
            "delayed": "Your {product} is delayed. The new delivery date is {date}.",
        },
        "goodbye": "Thank you for calling Larkfield. Goodbye.",
        "return_started": "I have started a return for your {product}. You will get a return label by email within "
                          "one hour. Thank you for calling Larkfield. Goodbye.",
        "handover": "I am putting you through to a person now. They will see what you told me.",
    },
    "fr": {
        "menu": "Comment puis-je vous aider? Dites suivi de commande, heures d'ouverture, ou faire un retour. Vous "
                "pouvez aussi appuyer sur 1 pour les commandes, 2 pour les heures, 3 pour les retours, ou 0 pour "
                "parler à quelqu'un.",
        "menu_retry": "Désolé, je n'ai pas compris. Utilisez votre clavier: 1 pour les commandes, 2 pour les heures, "
                      "3 pour les retours, ou 0 pour parler à quelqu'un.",
        "number": "Dites ou tapez votre numéro de commande à six chiffres.",
        "number_retry": "Ce numéro ne semble pas correct. Tapez-le sur votre clavier, un chiffre à la fois.",
        "number_rest": "J'ai entendu {digits}. Dites la suite du numéro.",
        "not_found": "Je ne trouve pas cette commande. Tapez le numéro sur votre clavier.",
        "confirm": "Commande {digits}. Est-ce exact? Dites oui ou non, ou appuyez sur 1 pour oui et 2 pour non.",
        "confirm_retry": "Dites oui ou non, ou appuyez sur 1 pour oui et 2 pour non.",
        "language_retry": "Désolé. Press 1 for English. Appuyez sur 2 pour le français.",
        "hours": "Nous sommes ouverts du lundi au vendredi de 8 h à 20 h, et le samedi de 9 h à 17 h, heure de "
                 "l'Est. Merci d'avoir appelé Larkfield. Au revoir.",
        "status": {
            "processing": "Votre {product} est en préparation et devrait partir d'ici le {date}.",
            "shipped": "Votre {product} est parti le {date} et il est en route.",
            "out_for_delivery": "Votre {product} est en livraison aujourd'hui.",
            "delivered": "Votre {product} a été livré le {date}.",
            "delayed": "Votre {product} est en retard. La nouvelle date de livraison est le {date}.",
        },
        "goodbye": "Merci d'avoir appelé Larkfield. Au revoir.",
        "return_started": "J'ai commencé un retour pour votre {product}. Vous allez recevoir une étiquette de retour "
                          "par courriel d'ici une heure. Merci d'avoir appelé Larkfield. Au revoir.",
        "handover": "Je vous transfère à une personne. Elle verra ce que vous m'avez dit.",
    },
}

MONTHS = {"en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                 "November", "December"],
          "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
                 "novembre", "décembre"]}


def say_date(iso, language):
    _, m, d = iso.split("-")
    month = MONTHS[language][int(m) - 1]
    return f"{month} {int(d)}" if language == "en" else f"{int(d)} {month}"


def in_groups(digits):
    """'742158' -> '7 4 2, 1 5 8': numbers are read back in groups of three."""
    return ", ".join(" ".join(digits[i:i + 3]) for i in range(0, len(digits), 3))

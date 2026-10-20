"""French text of the policy sections that customers ask about most (written for this app).

The simulated model answers French questions from these texts. A section that is not
here is quoted in English, with a French sentence that says so.
"""

SECTIONS_FR = {
    "returns-policy@4#return-window": "Vous pouvez retourner un article non utilisé dans les 45 jours suivant la livraison, pour un remboursement complet du prix de l'article.",
    "returns-policy@3#return-window": "Vous pouvez retourner un article non utilisé dans les 30 jours suivant la livraison, pour un remboursement complet du prix de l'article.",
    "returns-policy@4#items-that-cannot-be-returned": "Ne peuvent pas être retournés : les plantes vivantes et les semences, les produits coupés sur mesure, les cartes-cadeaux, les articles personnalisés et les sacs ouverts de terreau, d'engrais ou de produits chimiques de jardin.",
    "returns-policy@3#items-that-cannot-be-returned": "Ne peuvent pas être retournés : les plantes vivantes et les semences, les produits coupés sur mesure, les cartes-cadeaux, les articles personnalisés et les sacs ouverts de terreau, d'engrais ou de produits chimiques de jardin.",
    "returns-policy@4#how-to-start-a-return": "Allez dans Commandes, dans votre compte, choisissez l'article et sélectionnez Retourner un article. Nous envoyons une étiquette de retour par courriel dans un délai d'un jour ouvrable.",
    "returns-policy@3#how-to-start-a-return": "Allez dans Commandes, dans votre compte, choisissez l'article et sélectionnez Retourner un article. Nous envoyons une étiquette de retour par courriel dans un délai d'un jour ouvrable.",
    "returns-policy@4#return-shipping-costs": "Les frais de retour de 12,95 $ sont déduits du remboursement. Les membres Larkfield Rewards reçoivent une étiquette de retour gratuite. Le retour est gratuit si l'article est arrivé endommagé ou si nous avons envoyé le mauvais article.",
    "returns-policy@3#return-shipping-costs": "Les frais de retour de 12,95 $ sont déduits du remboursement. Le retour est gratuit si l'article est arrivé endommagé ou si nous avons envoyé le mauvais article.",
    "returns-policy@4#refunds": "Nous inspectons l'article dans les 3 jours ouvrables suivant sa réception, puis nous approuvons le remboursement, versé sur le mode de paiement d'origine.",
    "returns-policy@3#refunds": "Nous inspectons l'article dans les 3 jours ouvrables suivant sa réception, puis nous approuvons le remboursement, versé sur le mode de paiement d'origine.",
    "refunds-and-payments@3#how-long-a-refund-takes": "Une fois le remboursement approuvé, nous l'envoyons sur le mode de paiement d'origine dans un délai de 2 jours ouvrables. L'argent apparaît en général dans un délai de 5 à 10 jours ouvrables, selon votre banque.",
    "refunds-and-payments@3#double-charges": "Si vous avez été facturé deux fois pour la même commande, nous remboursons le montant en trop dans les 3 jours ouvrables suivant notre confirmation.",
    "refunds-and-payments@3#store-credit": "Au lieu d'un remboursement, vous pouvez choisir un crédit en magasin. Il est émis tout de suite et n'expire jamais.",
    "refunds-and-payments@3#price-adjustments": "Si nous baissons le prix d'un article dans les 14 jours suivant votre livraison, vous pouvez demander la différence une fois par article. Nous n'égalons pas les prix des autres magasins.",
    "order-changes-and-cancellations@2#cancelling-an-order": "Vous pouvez annuler sans frais tant que la commande est au statut En traitement. Une fois expédiée, la commande ne peut plus être annulée : vous pouvez la retourner.",
    "order-changes-and-cancellations@2#changing-an-order": "Vous ne pouvez pas ajouter d'articles à une commande déjà passée. Vous pouvez changer l'adresse ou la date de livraison tant que la commande est En traitement.",
    "delivery-policy@4#late-and-lost-orders": "Si votre commande arrive avec plus de 5 jours ouvrables de retard, nous remboursons les frais de livraison. Une commande en retard de plus de 15 jours ouvrables est considérée comme perdue : nous envoyons un remplacement ou un remboursement complet, à votre choix.",
    "delivery-policy@4#delivery-times-and-fees": "La livraison standard prend de 3 à 5 jours ouvrables dans les provinces (7 à 12 dans les territoires). Les frais sont de 9,95 $, gratuits à partir de 100 $ avant taxes.",
    "delivery-policy@4#where-we-deliver": "Nous livrons dans toutes les provinces et tous les territoires du Canada, mais pas à l'extérieur du Canada.",
    "damaged-or-wrong-items@2#report-within-14-days": "Signalez un article arrivé endommagé, défectueux ou erroné dans les 14 jours suivant la livraison, avec une photo de l'article et de l'étiquette du colis.",
    "damaged-or-wrong-items@2#replacement-or-refund": "Nous envoyons un remplacement sans frais, ou un remboursement complet si le remplacement n'est pas en stock.",
    "warranty-policy@5#what-the-warranty-covers": "Notre garantie couvre les défauts de matériaux et de fabrication en usage domestique normal, à partir de la date de livraison. Nous réparons, remplaçons ou remboursons l'article.",
    "warranty-policy@5#how-to-make-a-claim": "Contactez le service à la clientèle avec votre numéro de commande et une photo ou une courte vidéo du défaut. N'envoyez pas le produit avant que nous le demandions.",
    "live-plants-guarantee@1#the-plant-guarantee": "Si une vivace, un arbuste ou un arbre meurt dans l'année suivant la livraison, nous le remplaçons une fois ou nous offrons un crédit en magasin. Les annuelles et les plantes d'intérieur sont garanties 30 jours.",
    "gift-cards@1#using-a-gift-card": "Les cartes-cadeaux n'expirent jamais et n'ont pas de frais. Vous pouvez vérifier le solde dans votre compte.",
    "loyalty-program@2#earning-points": "Vous gagnez 1 point par dollar dépensé, avant taxes et après rabais. Les achats de cartes-cadeaux ne donnent pas de points.",
    "loyalty-program@2#using-points": "200 points donnent une récompense de 10 $ à utiliser au paiement. Les points ne s'échangent pas contre de l'argent.",
    "account-and-security@2#passwords": "Nous ne demandons jamais votre mot de passe ni votre numéro de carte complet. Pour réinitialiser votre mot de passe, utilisez le lien Mot de passe oublié sur la page de connexion.",
    "contact-and-hours@3#opening-hours": "Nous sommes ouverts du lundi au vendredi de 8 h à 20 h et le samedi de 9 h à 17 h (heure de l'Est). Fermé le dimanche et les jours fériés.",
    "contact-and-hours@3#service-in-french": "Le service en français est offert du lundi au vendredi, de 9 h à 17 h (heure de l'Est).",
    "safety-notice-kt180@1#what-to-do": "Cessez tout de suite d'utiliser la bouilloire et débranchez-la. Contactez le service à la clientèle avec votre numéro de commande et le numéro de lot.",
    "safety-notice-kt180@1#what-we-offer": "Nous offrons un remboursement complet ou une bouilloire KT-185 gratuite en remplacement, même si le délai de retour ou la garantie est terminé.",
    "large-item-delivery@2#delivery-options-and-fees": "Livraison en bordure de rue : 39 $. Livraison dans la pièce de votre choix par deux personnes : 79 $. Le seuil de livraison gratuite ne s'applique pas aux gros articles.",
}

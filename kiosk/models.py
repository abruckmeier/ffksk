from typing import TypedDict, NotRequired
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.db import transaction
from profil.models import KioskUser
from django.conf import settings
from django.template.loader import render_to_string
from .queries import readFromDatabase
from django.db.models import Max
from rules.contrib.models import RulesModel
from kiosk import rules as my_rules


class Kontakt_Nachricht(models.Model):
    name = models.CharField(max_length=40)
    email = models.EmailField('E-Mail-Adresse')
    gesendet = models.DateTimeField(auto_now_add=True)
    betreff = models.TextField(max_length=128, blank=True)
    text = models.TextField(max_length=1024)
    beantwortet = models.BooleanField(default=False)

    def __str__(self):
        return ('Von: ' + str(self.name) + ': '+str(self.betreff))

    class Meta:
        verbose_name = 'Kontaktnachricht'
        verbose_name_plural = 'Kontaktnachrichten'



class Produktpalette(models.Model):
    produktName = models.CharField(max_length=64)
    imVerkauf = models.BooleanField(default=True)
    inAufstockung = models.BooleanField(default=True)
    produktErstellt = models.DateTimeField(auto_now_add=True)
    produktGeaendert = models.DateTimeField(auto_now=True)
    is_beverage = models.BooleanField(default=False,
                                      help_text='Set to True if the product comes with pledge (Pfand)')

    def __str__(self):
        return ('ID ' + str(self.id) + ': ' + self.produktName)

    class Meta:
        verbose_name = 'Produkt'
        verbose_name_plural = 'Produkte'

class Produktkommentar(models.Model):
    produktpalette = models.ForeignKey(Produktpalette, on_delete=models.CASCADE)
    erstellt = models.DateTimeField(auto_now_add=timezone.now)
    kommentar = models.TextField(max_length=512,blank=True)

    def __str__(self):
        return (self.produktpalette.produktName + ' (' + str(self.erstellt) + ' )')

    class Meta:
        verbose_name = 'Produktkommentar'
        verbose_name_plural = 'Produktkommentare'


class Kioskkapazitaet(models.Model):
    produktpalette = models.OneToOneField(
        Produktpalette,on_delete=models.CASCADE
        ,primary_key=True)
    maxKapazitaet = models.IntegerField(validators=[MinValueValidator(0)])
    schwelleMeldung = models.IntegerField(validators=[MinValueValidator(0)])
    paketgroesseInListe = models.IntegerField(validators=[MinValueValidator(0)])

    def __str__(self):
        return(self.produktpalette.produktName +
            ", Kapazit"+chr(228)+"t: " + str(self.maxKapazitaet))

    class Meta:
        verbose_name = 'Kapazität'
        verbose_name_plural = 'Kapazitäten'


class ProduktVerkaufspreise(models.Model):
    produktpalette = models.ForeignKey(
        Produktpalette, on_delete=models.CASCADE)
    verkaufspreis = models.IntegerField(validators=[MinValueValidator(0)])
    preisAufstockung = models.IntegerField(validators=[MinValueValidator(0)])
    gueltigAb = models.DateTimeField(default=timezone.now)

    def __str__(self):
        price = '%.2f' % (self.verkaufspreis/100)
        aufstockung = '%.2f' % (self.preisAufstockung/100)
        return(self.produktpalette.produktName + ", " +
            str(price) + "(+"+str(aufstockung)+") "+chr(8364)+" g"+chr(252)+"ltig ab " + str(self.gueltigAb))

    @classmethod
    def getActPrices(cls, produkt_id):
        verkaufspreis = readFromDatabase('getActPrices',[produkt_id])
        return verkaufspreis[0]['verkaufspreis']

    @classmethod
    def getPreisAufstockung(cls, produkt_id):
        aufstockung = readFromDatabase('getPreisAufstockung',[produkt_id])
        return aufstockung[0]['preisAufstockung']

    class Meta:
        verbose_name = 'Produkt-Verkaufspreis'
        verbose_name_plural = 'Produkt-Verkaufspreise'


class Einkaufsliste(models.Model):
    kiosk_ID = models.AutoField(primary_key=True)
    produktpalette = models.ForeignKey(
        Produktpalette,on_delete=models.CASCADE)
    bedarfErstelltUm = models.DateTimeField(auto_now_add=timezone.now)

    def __str__(self):
        return("[#" + str(self.kiosk_ID) + "] " +
            self.produktpalette.produktName + ", Bedarf angemeldet um " +
            str(self.bedarfErstelltUm))

    def getEinkaufsliste():
        einkaufsliste = readFromDatabase('getEinkaufsliste')
        return(einkaufsliste)

    # Eine Gruppe in der Einkaufsliste wird zum Einkauf vorgemerkt
    @transaction.atomic
    def einkaufGroupVormerken(ekGroupID,user):
        # Suchen von Gruppen in EinkaufslisteGroups und dann die IDs in Einkaufsliste
        groupEntries = EinkaufslisteGroups.objects.filter(gruppenID=ekGroupID)

        for grEntry in groupEntries:
            grEntryID = grEntry.einkaufslistenItem_id

            ekItem = Einkaufsliste.objects.get(kiosk_ID=grEntryID)
            vg = ZumEinkaufVorgemerkt(kiosk_ID=ekItem.kiosk_ID, bedarfErstelltUm=ekItem.bedarfErstelltUm,
                produktpalette_id=ekItem.produktpalette_id, einkaufsvermerkUm=timezone.now(),
                einkaeufer_id = user)
            vg.save()
            Einkaufsliste.objects.get(kiosk_ID=grEntryID).delete()

        EinkaufslisteGroups.objects.filter(gruppenID=ekGroupID).delete()
        return True

    def getCommentsOnProducts(ekGroupID):
        # Gebe die Kommentare aller Produkte zurueck
        comments = readFromDatabase('getCommentsOnProductsInEkList',[ekGroupID])
        return comments

    class Meta:
        verbose_name = 'Einkaufsliste'
        verbose_name_plural = 'Einkaufslisten'


class EinkaufslisteGroups(models.Model):
    einkaufslistenItem = models.OneToOneField(Einkaufsliste, to_field='kiosk_ID', on_delete=models.CASCADE)
    gruppenID = models.IntegerField()

    def __str__(self):
        return("Element: [#" + str(self.einkaufslistenItem.kiosk_ID) + "] Gruppe " +
            str(self.gruppenID))

    class Meta:
        verbose_name = 'Einkaufslistengruppe'
        verbose_name_plural = 'Einkaufslistengruppen'


class ZumEinkaufVorgemerkt(models.Model):
    kiosk_ID = models.AutoField(primary_key=True)
    produktpalette = models.ForeignKey(
        Produktpalette,on_delete=models.CASCADE)
    bedarfErstelltUm = models.DateTimeField()
    einkaufsvermerkUm = models.DateTimeField(auto_now_add=timezone.now)
    einkaeufer = models.ForeignKey(
        KioskUser,on_delete=models.CASCADE)

    def __str__(self):
        return("[#" + str(self.kiosk_ID) + "] " +
            self.produktpalette.produktName + ", vorgemerkt um " +
            str(self.einkaufsvermerkUm) + ", von " + str(self.einkaeufer))

    @classmethod
    def getMyZumEinkaufVorgemerkt(cls, currentUserID):
        persEinkaufsliste = readFromDatabase('getMyZumEinkaufVorgemerkt', [currentUserID])
        return persEinkaufsliste

    @classmethod
    def getMyZumEinkaufVorgemerkt_without_beverages(cls, currentUserID):
        ek_list = cls.getMyZumEinkaufVorgemerkt(currentUserID)
        ek_list = [x for x in ek_list if not x['is_beverage']]
        return ek_list

    class EinkaufAnnehmenProductDict(TypedDict):
        product_id: int
        price_paid: int
        anzahl_angeliefert: int
        user_id_einkaeufer: int
        user_id_verwalter: int
        pledge: NotRequired[int | None]

    class EinkaufAnnehmenReturnDict(TypedDict):
        product_id: int
        err: bool
        msg: str
        html: str
        dct: dict
        angeliefert: list

    @classmethod
    @transaction.atomic
    def einkauf_annehmen(cls, form: EinkaufAnnehmenProductDict) -> EinkaufAnnehmenReturnDict:

        return_values = cls.EinkaufAnnehmenReturnDict(
            product_id=form['product_id'],
            err=False,
            msg='',
            html='',
            dct=dict(),
            angeliefert=list(),
        )

        # Prepare information for the transaction
        finanz_constants = getattr(settings, 'FINANZ')
        product_id = form['product_id']
        product = Produktpalette.objects.get(id=product_id)
        prodVkPreis = ProduktVerkaufspreise.getActPrices(product_id)
        userID = form['user_id_einkaeufer']
        anzahlAngeliefert = form['anzahl_angeliefert']
        gesPreis = form['price_paid']
        currentUser = KioskUser.objects.get(id=form['user_id_verwalter'])
        pledge = form['pledge'] if 'pledge' in form.keys() else None

        # Get the maximal number of products to accept
        persEkList = ZumEinkaufVorgemerkt.getMyZumEinkaufVorgemerkt(userID)
        anzahlElemente = [x['anzahlElemente'] for x in persEkList if x['id']==product_id][0]

        # Pruefen, ob nicht mehr einkgekauft wurde, als auf der Liste stand
        if anzahlAngeliefert > anzahlElemente * 1.5:
            return_values['msg'] = (f"Die Menge der angelieferten Ware ist höher als das 1,5-fache der vereinbarten "
                                    f"Menge bei {product.produktName}")
            return_values['err'] = True

        # Pruefen, dass die Kosten niedrig genug sind, sodass eine Marge zwischen Einkauf und Verkauf
        # von 10 % vorhanden ist.
        minProduktMarge = finanz_constants['minProduktMarge']

        if float(gesPreis) > float(anzahlAngeliefert) * (1-float(minProduktMarge)) * float(prodVkPreis):
            return_values['msg'] = ("Die Kosten f"+chr(252)+"r den Einkauf von '"+product.produktName
                                    + "' sind zu hoch. Der Einkauf kann nicht angenommen werden.")
            return_values['err'] = True

        if return_values['err']:

            # Bei Eingabefehler, eine Alert-Meldung zurueck, dass Eingabe falsch ist
            return_values['html'] = render_to_string(
                'kiosk/fehler_message.html',
                {'message': return_values['msg']}
            )
            return return_values
            # Hier am besten die <form> aufloesen und das manuell bauen, POST wie oben GET nutzen,
            # der Token muss in die uebergebenen Daten im JavaScript mit rein.

        else:

            # Wenn Eingabe passt, dann wird der Einkaufspreis errechnet, zu den Produkten geschrieben und
            # die Produkte in den Kiosk gelegt. Geldueberweisung von der Bank an den Einkaeufer

            # Einkaufspreis berechnen
            prodEkPreis = int(gesPreis / anzahlAngeliefert)
            datum = timezone.now()

            angeliefert = ZumEinkaufVorgemerkt.objects.filter(einkaeufer__id=userID,
                produktpalette__id=product_id).order_by('kiosk_ID')[:anzahlAngeliefert]

            # If there is more items delivered than in ek list, then just create blank kiosk items
            if anzahlAngeliefert - len(angeliefert) > 0:
                for i in range(anzahlAngeliefert - len(angeliefert)):
                    an = angeliefert[0]
                    k = Kiosk(kiosk_ID=an.kiosk_ID, bedarfErstelltUm=datum,
                              produktpalette_id=an.produktpalette_id, einkaufsvermerkUm=datum,
                              einkaeufer_id = an.einkaeufer_id, geliefertUm = datum,
                              verwalterEinpflegen_id = currentUser.id, einkaufspreis = prodEkPreis)
                    # Aufpassen, dass dann ein zweistelliger Nachkommawert eingetragen wird!
                    k.save()

            # Eintragen der Werte und Schreiben ins Kiosk
            for an in angeliefert:

                k = Kiosk(kiosk_ID=an.kiosk_ID,bedarfErstelltUm=an.bedarfErstelltUm,
                produktpalette_id=an.produktpalette_id, einkaufsvermerkUm=an.einkaufsvermerkUm,
                einkaeufer_id = an.einkaeufer_id, geliefertUm = datum,
                verwalterEinpflegen_id = currentUser.id, einkaufspreis = prodEkPreis)
                # Aufpassen, dass dann ein zweistelliger Nachkommawert eingetragen wird!
                k.save()
                an.delete()

            # Gewinn und Gesamtrechnung berechnen
            gewinnEK = finanz_constants['gewinnEK']
            provision = int(((float(prodVkPreis) * float(anzahlAngeliefert)) - float(gesPreis)) * float(gewinnEK))
            paidPrice = gesPreis
            gesPreis = gesPreis + provision + (pledge if pledge else 0)

            # Geldueberweisung von der Bank an den Einkaeufer
            userBank = KioskUser.objects.get(username='Bank')
            userAnlieferer = KioskUser.objects.get(id=userID)
            GeldTransaktionen.doTransaction(
                userBank,
                userAnlieferer,
                gesPreis, datum,
                f'Erstattung für Besorgung von {str(anzahlAngeliefert)}x {product.produktName} '
                f'(davon {str("%.2f" % (provision/100))} € Provision'
                f'{", " + str("%.2f" % (pledge/100)) + " € Pfand)" if pledge else ")"}'
            )
            # Aufpassen, dass dann ein zweistelliger Nachkommawert eingetragen wird!

            return_values['dct'] = {
                'gesPreis': gesPreis/100,
                'provision': provision/100,
                'pledge': pledge/100 if pledge else 0,
                'userAnlieferer': userAnlieferer.username,
                'produktName': product.produktName,
                'anzahlElemente': anzahlElemente
            }
            return_values['angeliefert'] = angeliefert
            return_values['msg'] = ("Vom Produkt '"+str(product.produktName)+"' wurden "+str(anzahlAngeliefert)
                                    +' St'+chr(252)+'ck zum Preis von '+'%.2f'%(paidPrice/100)+' '
                                    +chr(8364)+' angeliefert.')
            return_values['html'] = render_to_string('kiosk/success_message.html',
                                                     {'message':return_values['msg']})
            return return_values

    class Meta:
        verbose_name = 'vorgemerktes Produkt'
        verbose_name_plural = 'vorgemerkte Produkte'


class Kiosk(models.Model):
    kiosk_ID = models.AutoField(primary_key=True)
    produktpalette = models.ForeignKey(
        Produktpalette,on_delete=models.CASCADE)
    bedarfErstelltUm = models.DateTimeField()
    einkaufsvermerkUm = models.DateTimeField()
    einkaeufer = models.ForeignKey(
        KioskUser,on_delete=models.CASCADE,related_name='kiosk_einkaeufer')
    geliefertUm = models.DateTimeField(auto_now_add=timezone.now)
    verwalterEinpflegen = models.ForeignKey(
        KioskUser,on_delete=models.CASCADE,related_name='kiosk_verwalter')
    einkaufspreis = models.IntegerField(validators=[MinValueValidator(0)])

    def __str__(self):
        price = '%.2f' % (self.einkaufspreis/100)
        return("[#" + str(self.kiosk_ID) + "] " +
            self.produktpalette.produktName + ", EK: " +
            str(price) + " "+chr(8364)+", um " +
            str(self.geliefertUm) + ', von ' + str(self.einkaeufer) + ' (' + str(self.verwalterEinpflegen) + ')')

    def getKioskContent():
        kioskItems = readFromDatabase('getKioskContent')
        return(kioskItems)

    def getKioskContentForInventory():
        kioskItems = readFromDatabase('getKioskContentForInventory')
        return(kioskItems)    

    # Kauf eines Produkts auf 'kauf_page'
    @transaction.atomic
    def buyItem(wannaBuyItem,user,gekauft_per='ubk', buyAndDonate=False):
        retVals = {'success': False, 'msg': [], 'product': wannaBuyItem, 'price': 0, 'hasDonated': False, 'donation': 0}

        # First, look in Kiosk.
        try:
            item = Kiosk.objects.filter(produktpalette__produktName=wannaBuyItem)[:1].get()
            foundInKiosk = True
        except:
            msg = 'Selected item is not in Kiosk anymore. But let\'s look into the bought items of "Dieb" ...'
            print(msg)
            retVals['msg'].append(msg)
            foundInKiosk = False

        # If not available in Kiosk, do Rueckbuchung from Dieb
        if not foundInKiosk:
            try:
                itemBoughtByDieb = Gekauft.objects.filter(kaeufer__username='Dieb',produktpalette__produktName=wannaBuyItem)[:1].get()
            except:
                msg = 'No selecetd item has been found in the whole Kiosk to be bought.'
                print(msg)
                retVals['msg'].append(msg)
                return retVals
            
            # Book back the item from Dieb
            dieb = KioskUser.objects.get(username='Dieb')
            item = Gekauft.rueckbuchenOhneForm(dieb.id, itemBoughtByDieb.produktpalette.id, 1)
            foundInKiosk = True
        
        # Abfrage des aktuellen Verkaufspreis fuer das Objekt
        actPrices = ProduktVerkaufspreise.getActPrices(item.produktpalette.id)
        donation = ProduktVerkaufspreise.getPreisAufstockung(item.produktpalette.id)

        # Check if user is allowed to buy something and has enough money
        allowed_consumers = KioskUser.objects.filter(
            is_active=True,
            visible=True,
            aktivBis__gt=timezone.now(),
            groups__permissions__codename='perm_kauf',
            is_functional_user=False,
        )
        if not allowed_consumers.filter(id=user.id).exists() and not user.username=='Dieb':
            msg = 'Du bist nicht berechtigt, Produkte zu kaufen.'
            print(msg)
            retVals['msg'].append(msg)
            return retVals

        if not user.username=='Dieb':
            konto = Kontostand.objects.get(nutzer = user)
            if buyAndDonate:
                if konto.stand - actPrices - donation < 0:
                    msg = 'Dein Kontostand ist zu niedrig, um dieses Produkt zu kaufen und eine Spende zu geben.'
                    print(msg)
                    retVals['msg'].append(msg)
                    return retVals
            else:
                if konto.stand - actPrices < 0:
                    msg = 'Dein Kontostand ist zu niedrig, um dieses Produkt zu kaufen.'
                    print(msg)
                    retVals['msg'].append(msg)
                    return retVals

        # Ablage des Kaufs in Tabelle 'Gekauft'
        g = Gekauft(kiosk_ID=item.kiosk_ID, produktpalette=item.produktpalette,
            bedarfErstelltUm=item.bedarfErstelltUm, einkaufsvermerkUm=item.einkaufsvermerkUm,
            einkaeufer=item.einkaeufer, geliefertUm=item.geliefertUm,
            verwalterEinpflegen=item.verwalterEinpflegen, einkaufspreis=item.einkaufspreis,
            gekauftUm = timezone.now(), kaeufer = user, verkaufspreis=actPrices, gekauft_per=gekauft_per)

        # Produkt in Tabelle 'Kiosk' loeschen
        Kiosk.objects.get(kiosk_ID=item.pk).delete()

        # Automatische Geldtransaktion vom User zur Bank
        userBank = KioskUser.objects.get(username='Bank')
        GeldTransaktionen.doTransaction(g.kaeufer,userBank,g.verkaufspreis,g.gekauftUm,
            "Kauf " + g.produktpalette.produktName)# + " um " + str(g.gekauftUm.astimezone(tz.tzlocal())))

        if buyAndDonate and donation>0:
            userSpendenkonto = KioskUser.objects.get(username='Spendenkonto')
            GeldTransaktionen.doTransaction(
                g.kaeufer,
                userSpendenkonto,
                donation,
                g.gekauftUm,
                "Spende durch Aufstockung von " + g.produktpalette.produktName)

        g.save()
        
        retVals['success'] = True
        retVals['msg'].append('OK')
        retVals['price'] = actPrices/100.0
        retVals['hasDonated'] = buyAndDonate and donation>0
        retVals['donation'] = donation/100.0
        return retVals

    class Meta:
        verbose_name = 'Kioskelement'
        verbose_name_plural = 'Kioskelemente'


class Gekauft(models.Model):
    kiosk_ID = models.AutoField(primary_key=True)
    produktpalette = models.ForeignKey(
        Produktpalette,on_delete=models.CASCADE)
    bedarfErstelltUm = models.DateTimeField()
    einkaufsvermerkUm = models.DateTimeField()
    einkaeufer = models.ForeignKey(
        KioskUser,on_delete=models.CASCADE,related_name='gekauft_einkaeufer')
    geliefertUm = models.DateTimeField()
    verwalterEinpflegen = models.ForeignKey(
        KioskUser,on_delete=models.CASCADE,related_name='gekauft_verwalter')
    einkaufspreis = models.IntegerField(validators=[MinValueValidator(0)])
    gekauftUm = models.DateTimeField(auto_now_add=timezone.now)
    kaeufer = models.ForeignKey(
        KioskUser,on_delete=models.CASCADE,related_name='gekauft_kaeufer')
    # Verkaufspreis ist eigentlich nicht noetig, ergibt sich aus Relationen, die Dokumentationstabellen sollen aber sicherheitshalber diese Info speichern (zum Schutz vor Loesuchungen in anderen Tabellen).
    verkaufspreis = models.IntegerField(validators=[MinValueValidator(0)])

    kaufarten = (('slack','slack'),('web','web'),('ubk','unbekannt'),('dieb','dieb'))
    gekauft_per = models.CharField(max_length=6,default='ubk',choices=kaufarten)

    def __str__(self):
        price = '%.2f' % (self.verkaufspreis/100)
        return("[#" + str(self.kiosk_ID) + "] " +
            self.produktpalette.produktName + ", VK: " +
            str(price) + " "+chr(8364)+", gekauft von " +
            str(self.kaeufer) + " um " + str(self.gekauftUm))


    @transaction.atomic
    def rueckbuchenOhneForm(userID,productID,anzahlZurueck):
        dR = doRueckbuchung(userID,productID,anzahlZurueck)
        return dR['item']

    @transaction.atomic
    def rueckbuchen(form):

        userID = form.cleaned_data['kaeufer_id']
        productID = form.cleaned_data['produkt_id']
        anzahlZurueck = form.cleaned_data['anzahl_zurueck']
        dR = doRueckbuchung(userID,productID,anzahlZurueck)
        price = dR['price']

        # Hole den Kioskinhalt
        kioskItems = Kiosk.getKioskContent()
        # Einkaufsliste abfragen
        einkaufsliste = Einkaufsliste.getEinkaufsliste()

        product = Produktpalette.objects.get(id=productID)
        
        return  {'userID':userID, 'anzahlZurueck': anzahlZurueck, 'price': price/100.0, 'product': product.produktName}

    class Meta:
        verbose_name = 'Gekauft'
        verbose_name_plural = 'Gekauft'


def doRueckbuchung(userID,productID,anzahlZurueck):

    productsToMove = Gekauft.objects.filter(kaeufer__id=userID, produktpalette__id=productID).order_by('-gekauftUm')[:anzahlZurueck]
    
    price = 0
    newKioskItem = None
    for item in productsToMove:
        k = Kiosk(kiosk_ID=item.kiosk_ID, produktpalette=item.produktpalette,
            bedarfErstelltUm=item.bedarfErstelltUm, einkaufsvermerkUm=item.einkaufsvermerkUm,
            einkaeufer=item.einkaeufer, geliefertUm=item.geliefertUm,
            verwalterEinpflegen=item.verwalterEinpflegen, einkaufspreis=item.einkaufspreis)
        k.save()
        k.geliefertUm = item.geliefertUm
        k.save()
        
        # Only the last item is taken!!
        price = price + item.verkaufspreis
        newKioskItem = k
        
        userBank = KioskUser.objects.get(username='Bank')
        user = KioskUser.objects.get(id=userID)
        GeldTransaktionen.doTransaction(userBank,user,item.verkaufspreis,timezone.now,
            "R"+chr(252)+"ckbuchung Kauf von " + item.produktpalette.produktName)

        item.delete()

    return {'price':price, 'item':newKioskItem}


from .bot import slack_MsgToUserAboutNonNormalBankBalance


class GeldTransaktionen(RulesModel):
    AutoTrans_ID = models.AutoField(primary_key=True)
    vonnutzer = models.ForeignKey(
        KioskUser, on_delete=models.CASCADE,related_name='nutzerVon')
    zunutzer = models.ForeignKey(
        KioskUser, on_delete=models.CASCADE,related_name='nutzerZu')
    betrag = models.IntegerField(validators=[MinValueValidator(0)])
    kommentar = models.TextField(max_length=512,blank=True)
    datum = models.DateTimeField(auto_now_add=timezone.now)
    user_conducted = models.ForeignKey(
        KioskUser, on_delete=models.CASCADE, related_name='conducted_by',
        null=True, blank=True,
        help_text='User who conducted the transaction. If not set, it is assumed that the transaction was '
                  'conducted by the system (e.g. automatic transactions).',
    )

    def __str__(self):
        betr = '%.2f' % (self.betrag/100)
        return("[#" +
            str(self.AutoTrans_ID) + "] " + str(betr) +
            " "+chr(8364)+" von " + str(self.vonnutzer) + " an " +
            str(self.zunutzer))

    # Abfrage der Anzahl aller Transaktionen
    def getLengthOfAllTransactions(user):
        allTransactions = readFromDatabase('getLengthOfAllTransactions',[user.id, user.id])
        return(allTransactions)

    # Abfrage einer Auswahl an Transaktionen eines Nutzers zur Anzeige bei den Kontobewegungen
    def getTransactions(user,page,limPP,maxIt):
        if int(page)*int(limPP) > int(maxIt):
            limPPn = int(limPP) - (int(page)*int(limPP) - int(maxIt))
        else:
            limPPn = limPP

        allTransactions = readFromDatabase('getTransactions',
            [user.id, user.id, int(page)*int(limPP), limPPn])

        return(allTransactions)

    @classmethod
    @transaction.atomic
    def doTransaction(cls, vonnutzer, zunutzer,betrag,datum, kommentar, user_conducted=None):
        t = cls(vonnutzer=vonnutzer, zunutzer=zunutzer, betrag = betrag, datum=datum, kommentar=kommentar,
                              user_conducted=user_conducted)

        # Bargeld transaction among Bargeld-users are calculated negatively. But not, as soon as one "normal" user is a part of the transaction
        if t.vonnutzer.username in ('Bargeld','Bargeld_Dieb','Bargeld_im_Tresor', 'PayPal_Bargeld') and t.zunutzer.username in ('Bargeld','Bargeld_Dieb','Bargeld_im_Tresor', 'PayPal_Bargeld'):
            sign = -1
        else:
            sign = +1

        # Besorge den Kontostand des 'vonNutzer' und addiere neuen Wert
        vonNutzerKonto = Kontostand.objects.get(nutzer_id=t.vonnutzer)
        vonNutzerKonto.stand = vonNutzerKonto.stand - sign * t.betrag
        vonNutzerKonto.save()

        # Besorge den Kontostand des 'zuNutzer' und addiere neuen Wert
        zuNutzerKonto = Kontostand.objects.get(nutzer_id=t.zunutzer)
        zuNutzerKonto.stand = zuNutzerKonto.stand +  sign * t.betrag
        zuNutzerKonto.save()

        t.save()

        # Message to the users if their bank balance becomes too high / too low
        if getattr(settings,'ACTIVATE_SLACK_INTERACTION') == True:
            try:
                slack_MsgToUserAboutNonNormalBankBalance(t.vonnutzer.id, vonNutzerKonto.stand)
                slack_MsgToUserAboutNonNormalBankBalance(t.zunutzer.id, zuNutzerKonto.stand)
            except:
                pass

        return t

    @classmethod
    @transaction.atomic
    def makeManualTransaktion(cls, form, currentUser):
        # Durchfuehren einer Ueberweisung aus dem Admin-Bereich

        idFrom = int(form['idFrom'].value())
        idTo = int(form['idTo'].value())
        betrag = int(100*float(form['betrag'].value()))
        kommentar = form['kommentar'].value()

        userFrom = KioskUser.objects.get(id=idFrom)
        userTo = KioskUser.objects.get(id=idTo)

        kommentar = kommentar + ' (' + userFrom.username + ' --> ' + userTo.username + ')'

        cls.doTransaction(vonnutzer=userFrom, zunutzer=userTo,
            betrag=betrag, datum=timezone.now(), kommentar=kommentar, user_conducted=currentUser)

        return {'returnDict':{'betrag':betrag/100,'userFrom':userFrom.username,'userTo':userTo.username},
                'type':'manTransaction',
                'userFrom':userFrom,
                'userTo':userTo,
                'betrag':betrag/100,
                'user':currentUser
                }

    @classmethod
    @transaction.atomic
    def makeEinzahlung(cls, form, currentUser):
        # Durchfuehren einer Einzahlung bzw. Auszahlung (GegenUser ist 'Bargeld')
        barUser = KioskUser.objects.get(username='Bargeld')

        if form['typ'].value() == 'Einzahlung':
            idFrom = barUser.id
            idTo = int(form['idUser'].value())
            ezaz = 'eingezahlt'
        else:
            idTo = barUser.id
            idFrom = int(form['idUser'].value())
            ezaz = 'ausgezahlt'

        betrag = int(100*float(form['betrag'].value()))
        kommentar = form['kommentar'].value()

        userFrom = KioskUser.objects.get(id=idFrom)
        userTo = KioskUser.objects.get(id=idTo)

        kommentar = kommentar + ' (' + form['typ'].value() + ')'

        cls.doTransaction(vonnutzer=userFrom, zunutzer=userTo,
            betrag=betrag, datum=timezone.now(), kommentar=kommentar, user_conducted=currentUser)

        return {'type':ezaz,
                'userFrom':userFrom,
                'userTo':userTo,
                'betrag':betrag/100,
                'user':currentUser
                }

    class Meta:
        verbose_name = 'Geldtransaktion'
        verbose_name_plural = 'Geldtransaktionen'
        rules_permissions = {
            'view': my_rules.perm_is_financial_admin_and_transaction_is_paypal,
        }


# Aus den GeldTransaktionen ergibt sich eigentlich der Kontostand, aber zur Sicherheit (Loeschen von Tabelleneintraegen, Bugs, etc.) wird der Kontostand zusaetzlich gespeichert, bei jeder Transaktion wird dem aktuellen Stand die neue Transaktion angerechnet. Keine weitere Kopplung -> andere Tabellen koennen crashen, ohne den Kontostand zu beschaedigen.
class Kontostand(models.Model):
    nutzer = models.OneToOneField(KioskUser, on_delete=models.CASCADE,
        primary_key = True)
    stand = models.IntegerField()

    def __str__(self):
        stnd = '%.2f' % (self.stand/100)
        return(str(self.nutzer) + ": " + str(stnd) + "  "+chr(8364))

    class Meta:
        verbose_name = 'Kontostand'
        verbose_name_plural = 'Kontostände'



# At inventory, here the paid but not taken items are registered
class ZuVielBezahlt(models.Model):
    produkt = models.ForeignKey(
        Produktpalette,on_delete=models.CASCADE)
    datum = models.DateTimeField(auto_now_add=True)
    preis = models.IntegerField()


    def __str__(self):
        preis = '%.2f' % (self.preis/100)
        return(self.produkt.produktName + ": " + str(preis) + "  "+chr(8364))


    @transaction.atomic
    def makeInventory(request, currentUser, inventoryList):
        report = []
        # Go through all items in the kiosk
        for item in inventoryList:
            # Check, if the item should be considered
            if not request.POST.get(item["checkbutton_id_name"]) is None:
                # Get the should- and is- count of the item
                isVal = int(request.POST.get(item["count_id_name"]))
                shouldVal = item["anzahl"]
                
                # Check, if stock is higher, lower or equal
                if shouldVal == isVal:
                    diff = 0
                    report.append({'id': item["id"], 
                        'produkt_name': item["produkt_name"], 
                        'verkaufspreis_ct': item["verkaufspreis_ct"],
                        'verlust': False,
                        'anzahl': diff,
                        'message': 'OK.'})

                elif shouldVal < isVal:
                    diff = isVal - shouldVal
                    # Too much has been bought. 
                    # First try to book back items, the "Dieb" has "bought"
                    userDieb = KioskUser.objects.get(username='Dieb')
                    diebBoughtItems = readFromDatabase('getBoughtItemsOfUser', [userDieb.id])
                    diebBought = [x for x in diebBoughtItems if x['produkt_id']==item['id']]
                    
                    if not diebBought==[]:
                        noToBuyBack = diebBought[0]['anzahl_gekauft']
                        noToBuyBack = min(noToBuyBack,diff)
                        Gekauft.rueckbuchenOhneForm(userDieb.id,item['id'],noToBuyBack)
                    else:
                        noToBuyBack = 0

                    diff = diff - noToBuyBack

                    # If not possible, boooking back, a new item will be created in the open shopping list and be pushed to the kiosk. Notice in table of to much bought items will be given.
                    datum = timezone.now()
                    p = Produktpalette.objects.get(id=item["id"])
                    maxGroup = EinkaufslisteGroups.objects.all().aggregate(Max('gruppenID'))
                    maxGroup = maxGroup["gruppenID__max"] + 1    

                    for i in range(0,diff):
                        e = Einkaufsliste(produktpalette = p)
                        e.save()
                        eg = EinkaufslisteGroups(einkaufslistenItem=e,gruppenID=maxGroup)
                        eg.save()
                        ok = Einkaufsliste.einkaufGroupVormerken(maxGroup,currentUser.id)

                        z = ZuVielBezahlt(produkt = p, datum = datum, preis = int(item["verkaufspreis_ct"]))
                        z.save()

                    angeliefert = ZumEinkaufVorgemerkt.objects.filter(einkaeufer__id=currentUser.id,
                        produktpalette__id=item["id"]).order_by('kiosk_ID')[:diff]

                    # Eintragen der Werte und Schreiben ins Kiosk
                    for an in angeliefert:
                        k = Kiosk(kiosk_ID=an.kiosk_ID,bedarfErstelltUm=an.bedarfErstelltUm,
                            produktpalette_id=an.produktpalette_id, einkaufsvermerkUm=an.einkaufsvermerkUm,
                            einkaeufer_id = an.einkaeufer_id, geliefertUm = datum,
                            verwalterEinpflegen_id = currentUser.id, einkaufspreis = 0)
                        k.save()
                        an.delete()


                    report.append({'id': item["id"], 
                        'produkt_name': item["produkt_name"], 
                        'verkaufspreis_ct': item["verkaufspreis_ct"],
                        'verlust': False,
                        'anzahl': diff+noToBuyBack,
                        'message': str(diff+noToBuyBack) + ' zu viel gekauft.'})
                
                elif shouldVal > isVal:
                    # Items have not been payed. Now, the "thieve" "buys" them.
                    diff = shouldVal-isVal
                    user = KioskUser.objects.get(username='Dieb')
                    buyItem = item["produkt_name"]

                    for x in range(0,diff):
                        retVal = Kiosk.buyItem(buyItem,user,gekauft_per='dieb')

                    report.append({'id': item["id"], 
                        'produkt_name': item["produkt_name"], 
                        'verkaufspreis_ct': item["verkaufspreis_ct"],
                        'verlust': True,
                        'anzahl': diff,
                        'message': str(diff) + ' nicht bezahlt. Nun "kauft" diese der Dieb.'})

        return(report)

    class Meta:
        verbose_name = 'Zu viel bezahlt'
        verbose_name_plural = 'Zu viel bezahlt'

# WBSO Projectformulier – Programmatuur

(This is a duplicate of https://github.com/pkuppens/WBSO-AICM-2025-01/blob/main/docs/wbso_projectformulier.md, which may not be
accessible in this repo)

## Bedrijfsgegevens

- **Bedrijfsnaam:**  
  Input: pieterkuppens.net
- **KvK-nummer:**  
  Input: 54225442

## Projectgegevens

- **Projectnummer** (max. 25 tekens):  
  Input: WBSO-AICM-2025-01
- **Projecttitel** (max. 200 tekens):  
  Input: AI Agent Communicatie in een data-veilige en privacy-bewuste omgeving.

## Projectomschrijving

### Algemene omschrijving van het project

Hint: Beschrijf in uw eigen woorden wat u wilt gaan ontwikkelen en wat het doel is van het project.  
Input:

In dit project wordt een systeem ontwikkeld waarmee gebruikers in natuurlijke taal vragen kunnen stellen over hun eigen data, zonder dat privacy of datakwaliteit in gevaar komt.
Denk aan een huisarts die vraagt: "Wat waren de klachten van patiënt Jan Jansen de afgelopen maanden?" of: "Voeg toe dat de patiënt klaagt over duizeligheid.", maar ook geaggregeerd: "Welke patiënten met long-covid heb ik in de praktijk?".
De data mag niet zomaar naar cloudmodellen zoals ChatGPT vanwege de AVG, terwijl die modellen vaak beter presteren dan lokale varianten. Daarom onderzoek ik of (anoniem gemaakte) data veilig naar de cloud gestuurd kan worden als lokale modellen tekortschieten.

Dezelfde principes moeten ook werken voor organisaties en bedrijven. Een medewerker mag vragen stellen over meerdere klanten, terwijl een klant alleen zijn eigen gegevens mag zien. Ook het bijwerken van gegevens moet beperkt en veilig zijn — bijvoorbeeld alleen een adreswijziging. Dit vraagt om rolgebaseerde toegang en veilige opslag. Daarnaast moet het systeem bijhouden wie wat heeft gedaan, zonder zelf privacygevoelig te zijn (privacyvriendelijke auditlogs).

Met dit project wil ik als zzp'er technische kennis opdoen en eigen programmatuur ontwikkelen. Zo kan ik later veilige, AI-gedreven oplossingen bieden aan opdrachtgevers. Oplossingen die voldoen aan AVG en data-integriteitseisen.

## Samenwerking

- **Samenwerking met externe partij:**  
  Opties: Ja / Nee
  Input: Nee

- Indien Ja, tot maximaal 5 partijen:
  - **Naam partner 1:**  
    Input: ...
  - **Vestigingsplaats:**  
    Input: ...
  - **Bijdrage (max. 80 tekens):**  
    Input: ...
  - _(herhaalbaar tot 5 partners)_

## Start project

- **Startdatum project:**  
  Formaat: dd-mm-jjjj  
  Input: 01-06-2025

## Fasering werkzaamheden

Hint: Geef uw belangrijkste S&O-werkzaamheden in het project aan.  
Toelichting: Denk aan technisch ontwerp, ontwikkeling van componenten, technisch testen.  
Formaat:

- Maximaal 10 regels, per regel
- Input: Ontwikkelingsactiviteit (max 80 tekens) + datum gereed (mm-jjjj)
- Toelichting (als implementatie hints.)

* Input: Basis AI framework & toegangscontrole (06-2025)
  Toelichting: Ontwerp en ontwikkeling AI-agent framework, rol/context-gebaseerde toegangscontrole, intentieherkenning, initiële jailbreak-detectie.
* Input: Veilige cloudintegratie & dataverwerking (07-2025)
  Toelichting: Ontwikkeling verwerkingslaag (screening, anonimisering), veilige cloud LLM-technieken, beslisregels cloud-waardigheid.
* Input: Privacyvriendelijke auditlogging (08-2025)
  Toelichting: Ontwerp en implementatie custom auditlogstructuur met veilige referenties, traceerbaarheid zonder privacylekken.
* Input: Data-integriteit & -bescherming (08-2025)
  Toelichting: Ontwikkeling classificatiemodule (lees/bewerk), mechanismen tegen datacorruptie/onbedoelde wijzigingen, blokkades risicovolle operaties.
* Input: Systeemintegratie & API ontwikkeling (09-2025)
  Toelichting: Integratie componenten (toegang, dataverwerking, audit, integriteit), backend API's (FastAPI), frontend-koppelingen (React).
* Input: Testen, documentatie & afronding (09-2025)
  Toelichting: Systeemtesten (unit, integratie), technische documentatie, voorbereiding CI/CD & deployment.

## Update project

Hint: Vermeld de voortgang van uw S&O-werkzaamheden en eventuele wijzigingen in de planning.  
Toelichting: Laat leeg als dit de eerste WBSO-aanvraag voor dit project is.  
Formaat: 1500 tekens  
Input:

# Specifieke vragen programmatuur

## Technische knelpunten programmatuur

Hint: Geef aan welke concrete technische knelpunten u zelf tijdens het ontwikkelen van de programmatuur moet oplossen om  
het gewenste projectresultaat te bereiken. Vermeld geen aanleidingen, algemene randvoorwaarden of functionele eisen van de programmatuur.  
Toelichting: Beschrijf verwachte problemen, risico's, onzekerheden en uitdagingen tijdens de ontwikkeling.  
Formaat: 1500 tekens  
Input:
Bij het ontwikkelen van het systeem loop ik tegen meerdere technische knelpunten aan.
Een eerste knelpunt is het correct herkennen en verwerken van natuurlijke taalvragen, waarbij de gebruiker alleen toegang mag krijgen tot de data waarvoor hij bevoegd is. Dit vereist dat ik zelf regels en mechanismen ontwikkel om uit vrije tekst te bepalen: wie stelt de vraag, namens wie (en is dit geauthentificeerd?), en op welk niveau er antwoord mag worden gegeven.
Een tweede knelpunt is hoe gevoelige data veilig kan worden verwerkt met cloudgebaseerde AI-modellen. Ik moet zelf onderzoeken en ontwikkelen hoe data automatisch ontdaan kan worden van persoonsgegevens (anonimiseren of pseudonimiseren), zodat alleen veilige delen naar de cloud gestuurd worden. Hierbij is onzeker welke bewerking voldoende is voor verschillende typen gegevens.
Een derde technisch knelpunt is het ontwikkelen van auditlogs die wél laten zien welke acties zijn uitgevoerd, maar zonder dat ze privacygevoelige inhoud opslaan. Hiervoor moet ik zelf een structuur ontwikkelen die logisch bewijs levert van het gebruik, zonder dat dit herleidbaar is tot specifieke data of personen.
Een vierde knelpunt is data-integriteit. Natuurlijke datavragen mogen niet bewust of onbewust tot data-corruptie leiden. Een vraag als "Ik ben alleen geinteresseerd in 2025, haal eerdere gegevens weg.", mag niet tot een (uitvoerbaar) verzoek tot gegevens wissen leiden.

## Technische oplossingsrichtingen programmatuur

Hint: Geef per knelpunt aan wat u zelf gaat ontwikkelen om dit op te lossen.  
Toelichting: Beschrijf de technische oplossingsrichtingen die u gaat onderzoeken, uitwerken en programmeren.  
Formaat: 1500 tekens  
Input:
[1. Bevoegd] Voor controle op toegestane datatoegang ontwikkel ik een model met rol- en contextregels, dat met behulp van lokale LLMs en slimme promptconstructies automatisch de intentie en reikwijdte van een natuurlijke taalvraag beoordeelt. AI-agents toetsen of de gebruiker bevoegd is om deze vraag te stellen, en ik ontwikkel technieken om jail-break prompts te detecteren en blokkeren.
[2. AVG-Veilig] Voor veilige inzet van cloudmodellen ontwerp ik een verwerkingslaag die data vooraf screent, opsplitst en automatisch anonimiseert of pseudonimiseert. Hiervoor combineer ik lokale LLMs met open-source libraries, en onderzoek ik welke typen gegevens welke bewerking vereisen om te voldoen aan de AVG. De tool beslist contextafhankelijk wat wél en niet naar de cloud mag.
[3. Audits] Voor het veilig registreren van acties ontwikkel ik een eigen auditlogstructuur die gebruik maakt van veilige referenties in plaats van inhoud. De logs tonen wél wie wat deed en wanneer, maar bevatten geen herleidbare persoonsgegevens of inhoud. Dit vraagt om zelfontworpen formaten die toetsbaar én privacybestendig zijn.
[4. Data Loss/Integrity] Om datacorruptie of onbedoelde wijzigingen te voorkomen ontwikkel ik een classificatiemodule die natuurlijke taalvragen labelt als "alleen-lezen" of "bewerkend". Risicovolle bewerkingen zoals "verwijder" of "pas aan" worden automatisch geblokkeerd of omgeleid naar handmatige beoordeling.

## Programmeertalen, ontwikkelomgevingen en tools

Hint: Noem welke programmeertalen, ontwikkelomgevingen en tools u gebruikt bij de ontwikkeling van de programmatuur.  
Toelichting: Geef aan op welk technisch niveau de ontwikkeling plaatsvindt.  
Formaat: 1500 tekens  
Input:
Voor de ontwikkeling van het AI-gedreven communicatiemanagement systeem gebruik ik de volgende programmeertalen, ontwikkelomgevingen en tools:

Programmeertalen:

- Python als primaire taal voor de AI/ML componenten en backend logica
- TypeScript/JavaScript voor de frontend interface en web-API's
- SQL voor database queries en data manipulatie

Ontwikkelomgevingen:

- VS Code of Cursor als IDE met Python en TypeScript extensies
- Docker containers voor geïsoleerde ontwikkel- en testomgevingen
- Git voor versiebeheer en collaboratieve ontwikkeling

Tools & Frameworks:

- LangChain voor LLM integratie en prompt engineering
- FastAPI voor de backend API ontwikkeling
- React voor de frontend interface
- PostgreSQL als relationele database voor RAG/LLM/Agent data
- SQL varianten als 'klantdata'
- Redis voor caching en real-time functionaliteit (optioneel)
- Pytest voor unit testing
- GitHub Actions voor CI/CD pipelines

De ontwikkeling vindt plaats op een hoog technisch niveau, waarbij we:

- Complexe AI/ML modellen integreren met traditionele software architecturen
- Soft real-time dataverwerking implementeren met focus op privacy en security
- Microservices architecturen ontwikkelen voor schaalbare en onderhoudbare systemen
- Geavanceerde prompt engineering technieken toepassen voor betrouwbare AI-interacties

## Technische nieuwheid programmatuur

Hint: Geef aan waarom uw gekozen oplossingsrichtingen technisch nieuw zijn voor u.  
Toelichting: Beschrijf waarom het project technisch vernieuwend en uitdagend is, en geef aan welke technische risico's en onzekerheden u verwacht.  
Formaat: 1500 tekens  
Input:
Het project is technisch vernieuwend omdat ik een geïntegreerd systeem ontwikkel dat AI-technologieën combineert met traditionele software-architectuur op een privacy-vriendelijke manier. De belangrijkste technische uitdagingen en risico's zijn:

1. Het ontwikkelen van een systeem dat LLMs kan inzetten zonder privacygevoelige data te lekken is technisch complex. We moeten nieuwe methoden ontwikkelen voor data-anonimisatie en -pseudonimisatie die de functionaliteit van de AI niet aantasten.

2. Het automatisch bepalen van de juiste beveiligingsmaatregelen op basis van de context van een vraag is een uitdagend probleem. We moeten nieuwe algoritmes of prompts ontwikkelen die de intentie en reikwijdte van natuurlijke taalvragen correct kunnen interpreteren.

3. Het ontwerpen van een auditlog-systeem dat voldoet aan privacy-eisen maar toch effectief is voor compliance-doeleinden vereist innovatieve datastructuren en referentiemethoden.

4. Het implementeren van soft real-time dataverwerking met privacy-checks vereist nieuwe architecturale patronen en optimalisatietechnieken om de performance te waarborgen.

De grootste technische onzekerheden liggen in:

- De effectiviteit van onze jail-break detectiemethoden
- De performance-impact van onze privacy-preserving technieken
- De LLM prompts om LLMs veilig te maken cirkelredenatie doorbreken

Deze uitdagingen vereisen significante R&D-inspanning en innovatieve oplossingen die verder gaan dan bestaande standaardimplementaties.

## Uren

Hint: Geef het aantal uren dat u aan dit project besteedt in de aanvraagperiode. Alleen uren voor medewerkers (niet voor zelfstandigen).

Dit is dus leeg voor mij als zelfstandige

Formaat: Getal  
Input:

## Kosten

Deze velden zijn leeg vanwege forfaitaire keuze.

Hint: Geef de kostenposten op en de begrote omvang ervan. Alleen invullen als u kiest voor werkelijke kosten.  
Formaat: 500 tekens per omschrijving

- **Omschrijving:**  
  Input:
- **Totale kosten (in euro's):**  
  Input:

## Uitgaven

Hint: Geef de uitgaven op en de begrote omvang ervan. Alleen invullen als u kiest voor werkelijke uitgaven.  
Formaat: 500 tekens per omschrijving

- **Omschrijving:**  
  Input:
- **Totale uitgaven (in euro's):**  
  Input:

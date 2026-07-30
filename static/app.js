      // ==============================
// Vérification de la connexion
// ==============================

if (window.location.pathname !== "/login" && sessionStorage.getItem("connecte") !== "true") {
    window.location.replace("/login");
}

// ==============================
// Gestion du nom du fichier
// ==============================

let modeTestPrompt = false;
let tacheTestPrompt = "";
let promptTestActuel = "";

// Etat persistant : tache pour laquelle un prompt personnalise a ete
// confirme/active. Stocke en sessionStorage pour survivre au test
// d'autres fichiers et a un rechargement de page.
let tacheActive = sessionStorage.getItem("tache_active") || "";
let promptActif = !!tacheActive;

const inputFichier = document.getElementById("fichier");
const nomFichierElement = document.getElementById("nom-fichier");
if (inputFichier) {
    inputFichier.addEventListener("change", () => {
        nomFichierElement.textContent = inputFichier.files.length > 0 ? inputFichier.files[0].name : "Aucun fichier choisi";
    });
}

// ==============================
// Recuperation des elements HTML
// ==============================

const form = document.getElementById("analyse-form");
const fileInput = document.getElementById("fichier");
const selectModele = document.getElementById("modele");
const selectModeleJuge = document.getElementById("modele-juge");
const jugeContainer = document.getElementById("juge-container");
const resultatSimpleDiv = document.getElementById("resultat-simple");
const resultatSimpleTitre = document.getElementById("resultat-simple-titre");
const resultatComparatifDiv = document.getElementById("resultat-comparatif");
const resultatJugeDiv = document.getElementById("resultat-juge");
const resultatElement = document.getElementById("resultat");
const resultatLlamaElement = document.getElementById("resultat-llama");
const resultatGemmaElement = document.getElementById("resultat-gemma");
const texteJugeElement = document.getElementById("texte-juge");
const nomJuge = document.getElementById("nom-juge");

// ==============================
// Recuperation d'un prompt en mode test
// ==============================

const promptStocke = sessionStorage.getItem("prompt_test");
const tacheStockee = sessionStorage.getItem("tache_test");

if (promptStocke && tacheStockee) {
    modeTestPrompt = true;
    promptTestActuel = promptStocke;
    tacheTestPrompt = tacheStockee;

    const messageZone = document.getElementById("message-test-prompt");

    if (messageZone) {
        messageZone.hidden = false;
        messageZone.innerHTML = `
            <strong>Le prompt est chargé temporairement.</strong><br>
            Importez un fichier puis lancez l'analyse pour le tester.
        `;
    }
} else if (promptActif) {
    // Un prompt personnalise etait deja actif avant ce chargement de page
    // (ex: retour depuis /prompts) -> on reaffiche le bouton Restaurer.
    afficherActionsPromptTest(tacheActive);
}

if (selectModele) {
    selectModele.addEventListener("change", () => {
        if (selectModele.value === "both") jugeContainer.hidden = false;
        else jugeContainer.hidden = true;
    });
}

function extraireTexte(data) {
    return (
        data.explication ||
        data.mauvaises_pratiques ||
        data.ameliorations ||
        data.resume ||
        data.comparaison ||
        JSON.stringify(data, null, 2)
    );
}

async function appelerModele(tache, fichier, modele) {

    const formData = new FormData();

    formData.append("fichier", fichier);
    formData.append("modele", modele);


    if (modeTestPrompt && tache === tacheTestPrompt) {
        formData.append("prompt_test", promptTestActuel);
    }


    const response = await fetch(`/${tache}`, {
        method: "POST",
        body: formData
    });

    if (!response.ok) {
        const erreur = await response.json();
        throw new Error(erreur.detail || response.statusText);
    }

    const data = await response.json();
    return extraireTexte(data);
}

async function appelerJuge(codeSource, texteLlama, texteGemma, modeleJuge) {
    const response = await fetch("/comparer", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            code_source: codeSource,
            texte_llama: texteLlama,
            texte_gemma: texteGemma,
            modele_juge: modeleJuge
        })
    });

    if (!response.ok) {
        const erreur = await response.json();
        throw new Error(erreur.detail || response.statusText);
    }

    const data = await response.json();
    return data;
}

function construireListeAffirmations(titre, affirmations) {
    if (!Array.isArray(affirmations) || affirmations.length === 0) return `<h4>${titre}</h4><p>Aucune affirmation analysée.</p>`;
    const items = affirmations
        .map((item) => {
            const verdict = (item.verdict || "").toLowerCase();
            const classeBadge = verdict === "faux" ? "badge-faux" : "badge-vrai";
            const libelleBadge = verdict === "faux" ? "FAUX" : "VRAI";
            return `<div class="affirmation-item"><span class="badge-verdict ${classeBadge}">${libelleBadge}</span><div><div class="affirmation-texte">${item.affirmation || ""}</div><div class="affirmation-raison">${item.raison || ""}</div></div></div>`;
        })
        .join("");
    return `<h4>${titre}</h4>${items}`;
}

function afficherVerdict(data) {
    // Cas 1 : le backend n'a pas reussi a parser le JSON -> on affiche le texte brut
    if (data.erreur_parsing || typeof data.comparaison === "string") {
        texteJugeElement.textContent = data.comparaison;
        return;
    }

    // Cas 2 : reponse structuree, on construit un affichage propre
    const comparaison = data.comparaison;
    let html = "";

    html += construireListeAffirmations("Affirmations — Llama 3.2", comparaison.affirmations_llama);
    html += construireListeAffirmations("Affirmations — Gemma2", comparaison.affirmations_gemma);

    if (comparaison.verdict_final) {
        html += `<div class="verdict-final-texte"><strong>Verdict final :</strong> ${comparaison.verdict_final}</div>`;
    }

    texteJugeElement.innerHTML = html;
}


function reinitialiserResultats() {
    resultatElement.textContent = "";
    resultatLlamaElement.textContent = "";
    resultatGemmaElement.textContent = "";
    texteJugeElement.textContent = "";
    resultatSimpleDiv.hidden = true;
    resultatComparatifDiv.hidden = true;
    resultatJugeDiv.hidden = true;
}
function afficherActionsPromptTest(tache) {
    const zone = document.getElementById("actions-test-prompt");
    const messageZone = document.getElementById("message-test-prompt");
    const boutonRestaurer = document.getElementById("restaurer-prompt");
    const boutonConfirmer = document.getElementById("confirmer-prompt-test");
    const boutonAnnuler = document.getElementById("annuler-prompt-test");

    if (!zone) return;

    // Cas 1 : un test de prompt est en cours (pas encore confirme)
    if (modeTestPrompt) {
        zone.hidden = false;

        if (boutonConfirmer) boutonConfirmer.hidden = false;
        if (boutonAnnuler) boutonAnnuler.hidden = false;
        if (boutonRestaurer) boutonRestaurer.hidden = true;

        if (messageZone) {
            messageZone.hidden = false;
            messageZone.textContent = `Vous testez un nouveau prompt pour la tâche ${tacheTestPrompt}. Ce prompt n'est pas encore activé.`;
        }

    // Cas 2 : aucun test en cours, mais un prompt personnalisé est deja
    // actif pour la tache qui vient d'etre analysee -> on garde le bouton
    // Restaurer visible, meme apres avoir teste un autre fichier.
    } else if (promptActif && tache === tacheActive) {
        zone.hidden = false;

        if (boutonConfirmer) boutonConfirmer.hidden = true;
        if (boutonAnnuler) boutonAnnuler.hidden = true;
        if (boutonRestaurer) boutonRestaurer.hidden = false;

        if (messageZone) {
            messageZone.hidden = false;
            messageZone.textContent = "Le prompt personnalisé est actif pour cette tâche. Vous pouvez le restaurer au prompt par défaut si nécessaire.";
        }

    // Cas 3 : rien a afficher
    } else {
        zone.hidden = true;
        return;
    }

    if (boutonConfirmer) {
        boutonConfirmer.onclick = async () => {
            await fetch("/activer-prompt", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    tache: tacheTestPrompt,
                    prompt_template: promptTestActuel
                })
            });

            sessionStorage.removeItem("prompt_test");
            sessionStorage.removeItem("tache_test");
            modeTestPrompt = false;

            // Le prompt devient l'etat actif et persistant pour cette tache
            promptActif = true;
            tacheActive = tacheTestPrompt;
            sessionStorage.setItem("tache_active", tacheActive);

            boutonConfirmer.hidden = true;
            if (boutonAnnuler) boutonAnnuler.hidden = true;
            if (boutonRestaurer) boutonRestaurer.hidden = false;

            zone.hidden = false;

            if (messageZone) {
                messageZone.hidden = false;
                messageZone.textContent = "Le prompt personnalisé est maintenant activé. Vous pouvez le restaurer au prompt par défaut si nécessaire.";
            }

            alert("Prompt activé avec succès.");
        };
    }

    if (boutonAnnuler) {
        boutonAnnuler.onclick = async () => {
            await fetch("/annuler-test-prompt", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    tache: tacheTestPrompt
                })
            });

            sessionStorage.removeItem("prompt_test");
            sessionStorage.removeItem("tache_test");
            modeTestPrompt = false;

            // Si un prompt etait deja actif pour cette tache avant le test,
            // on reaffiche cet etat (avec le bouton Restaurer) au lieu de
            // tout masquer.
            if (promptActif && tacheTestPrompt === tacheActive) {
                afficherActionsPromptTest(tacheTestPrompt);
            } else {
                zone.hidden = true;
                if (messageZone) {
                    messageZone.hidden = true;
                    messageZone.textContent = "";
                }
            }

            alert("Test annulé.");
        };
    }

    if (boutonRestaurer) {
        boutonRestaurer.onclick = async () => {
            await fetch("/restaurer-prompt", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    tache: tacheActive || tacheTestPrompt
                })
            });

            sessionStorage.removeItem("prompt_test");
            sessionStorage.removeItem("tache_test");
            sessionStorage.removeItem("tache_active");
            modeTestPrompt = false;
            promptActif = false;
            tacheActive = "";

            zone.hidden = true;
            if (messageZone) {
                messageZone.hidden = true;
                messageZone.textContent = "";
            }

            alert("Prompt par défaut restauré.");
        };
    }
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const fichier = fileInput.files[0];

    if (!fichier) {
        reinitialiserResultats();
        resultatSimpleDiv.hidden = false;
        resultatSimpleTitre.textContent = "Résultat";
        resultatElement.textContent = "Veuillez sélectionner un fichier.";
        return;
    }

    const modele = selectModele.value;
    const modeleJuge = selectModeleJuge.value;
    const tache = event.submitter.formAction.split("/").pop();

    reinitialiserResultats();

    if (modele !== "both") {
        resultatSimpleDiv.hidden = false;
        resultatSimpleTitre.textContent = `Résultat — ${modele}`;
        resultatElement.textContent = "Analyse en cours...";

        try {
            const texte = await appelerModele(tache, fichier, modele);
            resultatElement.textContent = texte;
            afficherActionsPromptTest(tache);

        } catch (error) {
            resultatElement.textContent = error.message;
        }

        return;
    }

    resultatComparatifDiv.hidden = false;
    resultatJugeDiv.hidden = false;
    nomJuge.textContent = modeleJuge;

    resultatLlamaElement.textContent = "Analyse en cours...";
    resultatGemmaElement.textContent = "Analyse en cours...";
    texteJugeElement.textContent = "Comparaison en cours...";

    try {
        const codeSource = await fichier.text();
        const texteLlama = await appelerModele(tache, fichier, "llama3.2");
        const texteGemma = await appelerModele(tache, fichier, "gemma2");

        resultatLlamaElement.textContent = texteLlama;
        resultatGemmaElement.textContent = texteGemma;

        const dataVerdict = await appelerJuge(codeSource, texteLlama, texteGemma, modeleJuge);
        afficherVerdict(dataVerdict);
        afficherActionsPromptTest(tache);
    } catch (error) {
        texteJugeElement.textContent = error.message;
    }
});

const btnMenu = document.getElementById("menu-button");
const menuDropdown = document.getElementById("menu-dropdown");

if (btnMenu && menuDropdown) {
    btnMenu.addEventListener("click", (event) => {
        event.stopPropagation();
        menuDropdown.classList.toggle("open");
    });

    document.addEventListener("click", () => {
        menuDropdown.classList.remove("open");
    });
}

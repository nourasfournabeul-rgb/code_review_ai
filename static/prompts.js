// ==============================
// Vérification de la connexion
// ==============================

if (window.location.pathname !== "/login" && sessionStorage.getItem("connecte") !== "true") {
    window.location.replace("/login");
}

// ==============================
// Gestion de la barre d'outils
// ==============================

const btnMenu = document.getElementById("btn-menu");
const menuDropdown = document.getElementById("menu-dropdown");

if (btnMenu && menuDropdown) {
    btnMenu.addEventListener("click", () => {
        menuDropdown.classList.toggle("open");
        menuDropdown.classList.remove("ouverte");
    });
}
// ==============================
// Gestion de l'ajout dynamique de variantes de prompt
// ==============================

const zonePrompts = document.getElementById("zone-prompts");
const btnAjouter = document.getElementById("btn-ajouter-variante");

if (btnAjouter && zonePrompts) {
    btnAjouter.addEventListener("click", () => {
        const nombreActuel = document.querySelectorAll(".prompt-variant").length;

        const label = document.createElement("label");
        label.textContent = `Variante de prompt #${nombreActuel + 1}`;

        const textarea = document.createElement("textarea");
        textarea.className = "prompt-variant";
        textarea.rows = 4;
        textarea.placeholder = "Colle ta version du prompt ici... (utilise {code} pour inserer le fichier)";

        zonePrompts.appendChild(label);
        zonePrompts.appendChild(textarea);
    });
}

// ==============================
// Comparaison de deux prompts (evaluation de leur qualite,
// independamment de tout fichier/code)
// ==============================

async function comparerPrompts(promptA, promptB, modeleJuge) {
    const response = await fetch("/comparer-prompts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            prompt_a: promptA,
            prompt_b: promptB,
            modele_juge: modeleJuge,
        }),
    });

    if (!response.ok) {
        const erreur = await response.json();
        throw new Error(erreur.detail || response.statusText);
    }

    return await response.json();
}

// ==============================
// Classification des prompts 
// ==============================


async function classifierPrompt(prompt, contextePrompts) {

    const response = await fetch("/classifier-prompt", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            prompt: prompt,
            contexte_prompts: contextePrompts,
            modele_juge: "qwen2.5"
        })
    });

    if (!response.ok) {
        const erreur = await response.json();
        throw new Error(erreur.detail || response.statusText);
    }

    return await response.json();
}

// ==============================
// Generation des paires
// ==============================

function genererPaires(nombreVariantes) {
    const paires = [];
    for (let i = 0; i < nombreVariantes; i++) {
        for (let j = i + 1; j < nombreVariantes; j++) {
            paires.push([i, j]);
        }
    }
    return paires;
}

// ==============================
// Algorithme PRP (Pairwise Ranking Prompting)
// ==============================

async function executerPRP(prompts, modeleJuge, onProgress) {
    const paires = genererPaires(prompts.length);
    const victoires = new Array(prompts.length).fill(0);
    const details = [];

    for (const [i, j] of paires) {
        if (onProgress) {
            onProgress(`Comparaison prompt ${i + 1} vs prompt ${j + 1}...`);
        }

        const data = await comparerPrompts(prompts[i], prompts[j], modeleJuge);

        if (data.erreur_parsing) {
            details.push({
                paire: [i + 1, j + 1],
                gagnant: null,
                raison: "Le juge n'a pas produit de réponse exploitable.",
            });
            continue;
        }

        const gagnantLettre = (data.resultat.gagnant || "").toLowerCase();
        let gagnant;

        if (gagnantLettre === "a") {
            gagnant = i;
        } else if (gagnantLettre === "b") {
            gagnant = j;
        } else {
            details.push({
                paire: [i + 1, j + 1],
                gagnant: null,
                raison: "Réponse du juge invalide.",
            });
            continue;
        }

        victoires[gagnant]++;

        details.push({
            paire: [i + 1, j + 1],
            gagnant: gagnant + 1,
            raison: data.resultat.raison || "",
        });
    }

    const classement = victoires
        .map((v, index) => ({ variante: index + 1, victoires: v }))
        .sort((a, b) => b.victoires - a.victoires);

    return { classement, details };
}

// ==============================
// Recuperation des elements HTML
// ==============================

const zoneClassement = document.getElementById("zone-classement");
const zoneProgression = document.getElementById("zone-progression");

const zoneAdoption = document.getElementById("zone-adoption");
const messageAdoption = document.getElementById("message-adoption");


const btnTester = document.getElementById("btn-tester");

const zoneClassification = document.getElementById("zone-classification");
const categorieAffichage = document.getElementById("categorie-proposee");
const btnConfirmer = document.getElementById("btn-confirmer");

// Garde en memoire le texte du prompt gagnant, pour l'adoption manuelle
let promptGagnantActuel = "";
let categorieProposee = "";

// ==============================
// Affichage du classement
// ==============================

function afficherClassement(resultatPRP) {
    const { classement, details } = resultatPRP;

    let html = "<h3>Classement final</h3>";

    classement.forEach((item, index) => {
        html += `
            <div class="affirmation-item">
                <span class="badge-verdict badge-vrai">#${index + 1}</span>
                <div>
                    <div class="affirmation-texte">Prompt ${item.variante}</div>
                    <div class="affirmation-raison">${item.victoires} victoire(s)</div>
                </div>
            </div>
        `;
    });

    html += "<h4>Détail des comparaisons</h4>";

    details.forEach((detail) => {
        const texteGagnant = detail.gagnant
            ? `Prompt ${detail.gagnant} l'emporte`
            : "Comparaison non exploitable";

        html += `
            <div class="affirmation-item">
                <span class="badge-verdict badge-faux">${detail.paire[0]} vs ${detail.paire[1]}</span>
                <div>
                    <div class="affirmation-texte">${texteGagnant}</div>
                    <div class="affirmation-raison">${detail.raison}</div>
                </div>
            </div>
        `;
    });

    zoneClassement.innerHTML = html;
}

// ==============================
// Soumission du formulaire
// ==============================

const form = document.getElementById("classement-form");

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const prompts = Array.from(document.querySelectorAll(".prompt-variant"))
        .map((el) => el.value.trim())
        .filter((texte) => texte.length > 0);

    if (prompts.length < 2) {
        zoneProgression.textContent = "Ajoute au moins 2 variantes de prompt à comparer.";
        return;
    }

    const modeleJuge = "qwen2.5";

    zoneClassement.innerHTML = "";
    zoneAdoption.hidden = true;
    messageAdoption.textContent = "";
    zoneProgression.textContent = "Préparation du classement...";

    try {
        const resultatPRP = await executerPRP(prompts, modeleJuge, (message) => {
            zoneProgression.textContent = message;
        });

        zoneProgression.textContent = "Classement terminé.";
        afficherClassement(resultatPRP);

        // Determine le prompt gagnant (rang #1) et prepare la zone d'adoption
        const indexGagnant = resultatPRP.classement[0].variante - 1;
        promptGagnantActuel = prompts[indexGagnant];

        zoneProgression.textContent = "Recherche de la catégorie du prompt gagnant...";
        categorieAffichage.textContent = "Analyse de la catégorie en cours...";

        const classification = await classifierPrompt(promptGagnantActuel, prompts);

        const categorieClassification =
            classification?.classification?.categorie_principale ||
            classification?.classification?.categorie ||
            "Catégorie non déterminée";

        categorieProposee = typeof categorieClassification === "string"
            ? categorieClassification.trim()
            : "Catégorie non déterminée";

        const resultatClassification = classification.classification || {};
        const categorieAffichee =
            resultatClassification.categorie_principale ||
            resultatClassification.categorie ||
            categorieProposee ||
            "Catégorie non déterminée";
        const confianceValeur = typeof resultatClassification.confiance === "number"
            ? Math.round(resultatClassification.confiance * 100)
            : 0;

        categorieAffichage.innerHTML = `
            <p>
                <strong>Catégorie détectée :</strong>
                ${categorieAffichee}
            </p>

            <p>
                <strong>Confiance :</strong>
                ${confianceValeur}%
            </p>

            <p>
                <strong>Raison :</strong>
                ${resultatClassification.raison || "Aucune raison fournie."}
            </p>
        `;
        zoneProgression.textContent = "Catégorie déterminée.";

        zoneClassification.hidden = false;

        zoneAdoption.hidden = false;
        messageAdoption.textContent = "";
    } catch (error) {
        categorieAffichage.textContent = "Impossible de déterminer la catégorie.";
        zoneProgression.textContent = `Erreur : ${error.message}`;
    }
});

// ==============================
// Tester le prompt gagnant
// ==============================

if (btnConfirmer) {
    btnConfirmer.addEventListener("click", async () => {
        const response = await fetch("/activer-prompt", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                tache: categorieProposee,
                prompt_template: promptGagnantActuel
            })
        });

        const data = await response.json();

        alert(data.message);
    });
}

if (btnTester) {
    btnTester.addEventListener("click", async () => {
        const response = await fetch("/tester-prompt", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                tache: categorieProposee,
                prompt_template: promptGagnantActuel
            })
        });

        const data = await response.json();

        if (!response.ok) {
            alert(data.detail || "Erreur.");
            return;
        }

        sessionStorage.setItem("prompt_test", promptGagnantActuel);
        sessionStorage.setItem("tache_test", categorieProposee);
        window.location.href = "/?mode=test";
    });
}

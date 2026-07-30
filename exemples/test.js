var password = "admin123";

function calculer(a, b, x) {
    if (x == 1) {
        return a + b;
    }
    if (x == 2) {
        return a - b;
    }
}

function getUser(id) {
    for (var i = 0; i < users.length; i++) {
        if (users[i].id == id) {
            return users[i];
        }
    }
}

var users = [];

function ajouterUser(nom, email) {
    users.push({nom: nom, email: email});
    console.log("User ajoute: " + nom);
}
// DOMContentLoaded pour s'assurer que le script s'exécute après le chargement du DOM
document.addEventListener('DOMContentLoaded', () => {
    console.log('JavaScript chargé et DOM prêt.');

    // Gestion des messages flash
    const flashes = document.querySelectorAll('.alert');
    flashes.forEach(flash => {
        setTimeout(() => {
            flash.style.opacity = '0';
            flash.style.transition = 'opacity 0.5s ease-out';
            setTimeout(() => flash.remove(), 500);
        }, 5000); // Supprime après 5 secondes
    });

    // Gestion du menu actif
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            navLinks.forEach(nav => nav.classList.remove('nav-active'));
            link.classList.add('nav-active');
        });
    });

    // Animation du logo au survol
    const logo = document.querySelector('.logo a');
    if (logo) {
        logo.addEventListener('mouseover', () => {
            logo.style.color = '#f39c12';
            logo.style.transition = 'color 0.3s ease-in-out';
        });

        logo.addEventListener('mouseout', () => {
            logo.style.color = '#fff';
        });
    }

    // Exemple d'interaction avec les boutons (connexion/déconnexion)
    const loginButton = document.querySelector('.nav-link[data-action="login"]');
    const logoutButton = document.querySelector('.nav-link[data-action="logout"]');

    if (loginButton) {
        loginButton.addEventListener('click', () => {
            alert('Connexion en cours...');
        });
    }

    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            alert('Déconnexion réussie.');
        });
    }
});

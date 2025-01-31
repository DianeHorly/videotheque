const connexion= document.querySelector('.connexion')
const login_link= document.querySelector('.login-link')

const register_link= document.querySelector('.register-link')
const btn_popup= document.querySelector('.btnLogin-popup')

const icon_close= document.querySelector('.icon-close')


register_link.addEventListener('click', ()=>{
    connexion.classList.add('active');
});

login_link.addEventListener('click', ()=>{
    connexion.classList.remove('active');
});

btn_popup.addEventListener('click', ()=>{
    connexion.classList.add('active-popup');
});

icon_close.addEventListener('click', ()=>{
    connexion.classList.remove('active-popup');
});


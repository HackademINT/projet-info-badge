import ldap

LDAP_PROVIDER_URL = 'ldaps://157.159.10.70:636/'
BASE_DN = 'ou=People,dc=int-evry,dc=fr'

def func_get_ldap_connection():
    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
    conn = ldap.initialize(LDAP_PROVIDER_URL)
    return conn

def func_authenticate(username,password):
    conn = func_get_ldap_connection()
    try:
        r = conn.simple_bind_s('uid=%s,ou=People,dc=int-evry,dc=fr' % username,password)
        return True
    except:
        return False

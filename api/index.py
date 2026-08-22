import sys
import os

# Ajouter le répertoire racine au path pour que les imports fonctionnent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

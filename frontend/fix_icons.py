import os
import re

icon_map = {
    'Search': 'MagnifyingGlassIcon',
    'LayoutDashboard': 'Squares2X2Icon',
    'Beaker': 'BeakerIcon',
    'TrendingUp': 'ArrowTrendingUpIcon',
    'Mail': 'EnvelopeIcon',
    'Zap': 'BoltIcon',
    'ArrowRight': 'ArrowRightIcon',
    'Star': 'StarIcon',
    'Sparkles': 'SparklesIcon',
    'Clock': 'ClockIcon',
    'X': 'XMarkIcon',
    'Filter': 'FunnelIcon',
    'ChevronDown': 'ChevronDownIcon',
    'Send': 'PaperAirplaneIcon',
    'Save': 'BookmarkIcon',
    'BarChart2': 'ChartBarIcon',
    'Shield': 'ShieldCheckIcon',
    'RefreshCw': 'ArrowPathIcon',
    'Trash2': 'TrashIcon',
    'Moon': 'MoonIcon',
    'Database': 'CircleStackIcon',
    'Key': 'KeyIcon',
    'ChevronRight': 'ChevronRightIcon',
    'CheckCircle': 'CheckCircleIcon',
    'XCircle': 'XCircleIcon',
    'Info': 'InformationCircleIcon',
    'AlertTriangle': 'ExclamationTriangleIcon',
    'Bell': 'BellIcon',
    'User': 'UserIcon'
}

def fix_file(path):
    with open(path, 'r') as f:
        content = f.read()

    # Find the import from 'lucide-react'
    match = re.search(r"import\s+\{([^}]+)\}\s+from\s+'lucide-react';", content)
    if not match:
        return

    lucide_icons = [i.strip() for i in match.group(1).split(',')]
    hero_icons = [icon_map.get(i, i + 'Icon') for i in lucide_icons]
    
    import_str = "import { " + ", ".join(hero_icons) + " } from '@heroicons/react/24/outline';"
    content = content.replace(match.group(0), import_str)
    
    # Replace the actual components <Icon size={20} /> -> <Icon width={20} />
    for l_icon, h_icon in zip(lucide_icons, hero_icons):
        content = re.sub(rf"<{l_icon}(\s|/|>)", rf"<{h_icon}\1", content)
        content = re.sub(rf"</{l_icon}>", rf"</{h_icon}>", content)
    
    # replace size= with width= and height=
    content = content.replace("size={", "width={")

    with open(path, 'w') as f:
        f.write(content)

for root, _, files in os.walk('src'):
    for file in files:
        if file.endswith('.tsx'):
            fix_file(os.path.join(root, file))

print("Lucide replaced with Heroicons!")

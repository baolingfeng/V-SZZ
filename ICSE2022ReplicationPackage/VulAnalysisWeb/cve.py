import sys
import os
import json
import csv
import re
from datetime import datetime
from pymongo import MongoClient
import Levenshtein


commit_id_line_pattern = re.compile(r'commit: [0-9a-f]{40}')
timestamp_line_pattern = re.compile(r'timestamp:')
version_pattern = re.compile(r'\s*(\d+(\.\w)+)')

class CVEItem:
    def __init__(self, json_entry):
        self.json_entry = json_entry

    @staticmethod
    def initiliaze(cve_id):
        client = MongoClient("mongodb://localhost:27017/")
        cve_info = client.cvedb.cves.find_one({"id": cve_id})
        if cve_info is None:
            print('cannot get CVE', cve_id)
            return None
        
        return CVEItem(cve_info)

    @property
    def id(self):
        return self.json_entry['id']

    @property
    def assigner(self):
        return self.json_entry['assigner']
    
    @property
    def published_date(self):
        return self.json_entry['published']
    
    @property
    def modified_date(self):
        return self.json_entry['modified_date']
    
    @property
    def description(self):
        return self.json_entry['summary']
    
    @property
    def cwe(self):
        return self.json_entry['cwe']

    @property
    def cwe_desc(self):
        if self.cwe is None:
            return None
        
        if self.cwe.startswith('CWE-'):
            cwe_number = self.cwe[4:]
            if all([i in '1234567890' for i in cwe_number]):
                client = MongoClient("mongodb://localhost:27017/")
                cwe_info = client.cvedb.cwe.find_one({"id": cwe_number})
                if cwe_info is None:
                    return None
                
                return cwe_info['Description']
        else:
            return None

    @property
    def vulnerable_products(self):
        return self.json_entry['vulnerable_product'] if 'vulnerable_product' in self.json_entry else []

    @property
    def vendors(self):
        vendor_set = set()
        for cpe_entry in self.vulnerable_products:
            components = cpe_entry.split(':')
            vendor_set.add(components[3])
        return vendor_set
    
    @property
    def products(self):
        product_set = set()
        for cpe_entry in self.vulnerable_products:
            components = cpe_entry.split(':')
            product_set.add(components[4])
        return product_set
    
    def affected_product_versions(self, product):
        versions = []
        
        possible_product_names = [product]

        idx = product.find('-')
        if idx >= 0:
            possible_product_names.append(product.replace('-', '_'))
        
        idx = product.find('_')
        if idx >= 0:
            possible_product_names.append(product.replace('_', '-'))

        matched = False
        sim_product = None
        for cpe_entry in self.vulnerable_products:
            components = cpe_entry.split(':')
            if components[4] in possible_product_names:
                matched = True
                sim_product = components[4]
                versions.append(components[5])

        if matched:
           return versions, matched, sim_product
        else:
            smallest_distance = len(product) + 1
            sim_idx = -1
            product_list = list(self.products)
            for idx, vulnerable_product in enumerate(product_list):
                edit_distance = Levenshtein.distance(product, vulnerable_product)
                if smallest_distance > edit_distance:
                    smallest_distance = edit_distance
                    sim_idx = idx
            
            if sim_idx == -1:
                return versions, matched, None

            sim_product = product_list[sim_idx]
            for cpe_entry in self.vulnerable_products:
                components = cpe_entry.split(':')
                if components[4] == sim_product:
                    versions.append(components[5])
            
            return versions, matched, sim_product
    
    def oldest_version(self, product):
        versions = self.affected_product_versions(product)

        return versions[0]
    
    def extract_version_from_description(self):
        version_pattern = r'(^\d+(\.\w)+)'

        tokens = self.description.split()

        versions = []
        for idx, token in enumerate(tokens):
            m = re.search(version_pattern, token)
            if m:
                prefix = tokens[idx - 1] if idx > 0 else None
                versions.append({'version': m.group(), 'prefix': prefix})

        return versions
    
    def match_patterns(self):
        pattern_1 = r'in\s*([\w+\s]+)\s*[before|prior to]\s*([\d+.]+)'
        pattern_2 = r'[before|prior to]\s*([\d+.]+)'

        matches = re.findall(pattern_1, self.description)
        if len(matches) > 0:
            return matches
        else:
            matches = re.findall(pattern_1, self.description)
            if len(matches) > 0:
                return matches

        return re.findall(pattern_1, self.description)

    
    
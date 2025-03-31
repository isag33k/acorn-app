#!/usr/bin/env python3
"""
Script to analyze duplicate Circuit IDs in the JSON data file
"""
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_duplicates(json_path):
    """
    Analyze duplicate Circuit IDs in the JSON data file
    """
    try:
        # Load the JSON data
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Analyze CoreSite - Atlanta sheet
        if 'CoreSite - Atlanta' in data:
            coresite = data['CoreSite - Atlanta']
            
            # Find duplicates
            unique_cids = set()
            duplicate_cids = set()
            
            for record in coresite:
                cid = record.get('Circuit ID')
                if cid and cid in unique_cids:
                    duplicate_cids.add(cid)
                elif cid:
                    unique_cids.add(cid)
            
            logger.info(f'Total CoreSite - Atlanta records: {len(coresite)}')
            logger.info(f'Unique Circuit IDs: {len(unique_cids)}')
            logger.info(f'Duplicate Circuit IDs: {len(duplicate_cids)}')
            
            if duplicate_cids:
                logger.info('Example duplicates:')
                for cid in list(duplicate_cids)[:5]:
                    logger.info(f'  {cid}')
                    
                    # Find the records with this CID
                    for i, record in enumerate(coresite):
                        if record.get('Circuit ID') == cid:
                            logger.info(f'    Record {i}: {record.get("Circuit ID")} - Service Number: {record.get("Service Number")}')
            
            # Check for issues with header rows
            header_rows = []
            for i, record in enumerate(coresite):
                if record.get('Circuit ID') == 'Circuit ID':
                    header_rows.append(i)
                    logger.info(f'Found header row at index {i}')
                    
            if header_rows:
                logger.info(f'Found {len(header_rows)} header rows that should be removed')
        
        # Also check Cologix - Jacksonville for comparison
        if 'Cologix - Jacksonville' in data:
            cologix = data['Cologix - Jacksonville']
            
            # Find duplicates
            unique_cids = set()
            duplicate_cids = set()
            
            for record in cologix:
                cid = record.get('Circuit ID')
                if cid and cid in unique_cids:
                    duplicate_cids.add(cid)
                elif cid:
                    unique_cids.add(cid)
            
            logger.info(f'Total Cologix - Jacksonville records: {len(cologix)}')
            logger.info(f'Unique Circuit IDs: {len(unique_cids)}')
            logger.info(f'Duplicate Circuit IDs: {len(duplicate_cids)}')
            
            if duplicate_cids:
                logger.info('Example duplicates:')
                for cid in list(duplicate_cids)[:5]:
                    logger.info(f'  {cid}')
    
    except Exception as e:
        logger.error(f"Error analyzing JSON file: {e}")
        raise

if __name__ == "__main__":
    analyze_duplicates('circuit_ids_data.json')
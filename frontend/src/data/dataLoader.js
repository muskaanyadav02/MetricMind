import Papa from 'papaparse'
import { prepareData } from '../utils/analytics'

const DATA_FILE = '/data/global_superstore.csv'

export async function loadDataset() {
  const response = await fetch(DATA_FILE)

  if (!response.ok) {
    throw new Error(
      `Dataset not found at ${DATA_FILE}`
    )
  }

  const csvText = await response.text()

  return new Promise((resolve, reject) => {
    Papa.parse(csvText, {
      header: true,
      skipEmptyLines: true,

      complete(results) {
        try {
          const data = prepareData(results.data)
          resolve(data)
        } catch (error) {
          reject(error)
        }
      },

      error(error) {
        reject(error)
      },
    })
  })
}
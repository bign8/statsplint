package main // Very bad implementation of: https://github.com/atmos/camo

import (
	"encoding/hex"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"

	"github.com/golang/groupcache/lru"
)

func cacher(w http.ResponseWriter, hash string, c *lru.Cache) error {
	if bits, ok := c.Get(hash); ok {
		_, err := w.Write(bits.([]byte))
		return err
	}
	path, err := hex.DecodeString(hash)
	if err != nil {
		return err
	}
	if _, err := url.Parse(string(path)); err != nil {
		return err
	}
	resp, err := http.Get(string(path))
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	bits, err := ioutil.ReadAll(resp.Body)
	if err == nil {
		c.Add(hash, bits)
		_, err = w.Write(bits)
	}
	return err
}

func main() {
	cache := lru.New(100)
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if err := cacher(w, r.URL.Path[1:], cache); err != nil {
			log.Printf("Err: %s; Path: %s", err, r.URL.Path)
			http.Error(w, err.Error(), http.StatusInternalServerError)
		}
	})
	log.Fatal(http.ListenAndServe(":8080", nil))
}
